"""tests/test_ingestor_contract.py — 采集层契约测试

**不需要 API Key，不访问网络。** 用一个假 Ingestor 验证：

1. :class:`ingestors.base.Ingestor` 协议可被结构化检查通过
2. 任何 Ingestor 的产出都能通过契约校验
3. 产出能原样写进由 ``schema/market.sql`` 建的库，并满足
   ``adjusted_close = close * forward_factor``
4. 换数据源（换 Ingestor）时 writer 与下游完全不用改

第 4 条是本项目对「数据源可替换」这一主张的实际证据 ——
如果只写了一个参考实现，这条无法证明。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ingestors.base import (
    ContractViolation,
    Ingestor,
    IngestorInfo,
    check_factor_consistency,
    validate,
)
from ingestors.fuyao.writer import DuckDbMarketWriter, new_batch_id
from schema.ddl import table_columns

SCHEMA_SQL = (Path(__file__).resolve().parent.parent / "schema" / "market.sql").read_text()


class FakeIngestor:
    """一个完全不依赖上游的数据源 —— 合成数据，结构与契约一致。

    它的存在就是为了证明：换数据源时，除 Ingestor 实现外的一切都不用动。
    """

    def __init__(self, n_days: int = 400, n_symbols: int = 3):
        self.n_days = n_days
        self.n_symbols = n_symbols
        self._codes = [f"{600000 + i}.SH" for i in range(n_symbols)]

    def describe(self) -> IngestorInfo:
        return IngestorInfo(
            name="fake",
            homepage="(none)",
            credential_env="(none)",
            credential_help="(none)",
            notes="测试用合成数据源",
        )

    def list_symbols(self) -> pd.DataFrame:
        return validate(
            pd.DataFrame(
                [
                    {
                        "thscode": c, "ticker": c.split(".")[0], "name": f"合成{i}",
                        "exchange": "SH", "asset_type": "a-share", "currency": "CNY",
                    }
                    for i, c in enumerate(self._codes)
                ]
            ),
            "dim_symbol",
        )

    def _bars(self, thscode: str) -> pd.DataFrame:
        dates = pd.date_range("2024-01-01", periods=self.n_days, freq="D")
        rng = np.random.default_rng(abs(hash(thscode)) % (2**32))
        close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, self.n_days)))
        return pd.DataFrame(
            {
                "thscode": thscode,
                "date": dates,
                "open": close * 0.995,
                "high": close * 1.01,
                "low": close * 0.99,
                "close": close,
                "volume": rng.integers(1e6, 5e6, self.n_days),
                "turnover": rng.integers(1e8, 5e8, self.n_days),
                "currency": "CNY",
                "interval": "1d",
                "adjusted": "none",
            }
        )

    def fetch_daily_bars(self, thscode: str, start: str, end: str) -> pd.DataFrame:
        return validate(self._bars(thscode), "raw_kline_daily")

    def fetch_adjust_factors(self, thscode: str, start: str, end: str) -> pd.DataFrame:
        bars = self._bars(thscode)
        rng = np.random.default_rng(7)
        fwd = rng.uniform(0.8, 1.2, self.n_days)
        return validate(
            pd.DataFrame(
                {
                    "thscode": thscode,
                    "date": bars["date"],
                    "forward_factor": fwd,
                    "backward_factor": 1.0 / fwd,
                }
            ),
            "calc_adjust_factor_daily",
        )


# --- 1. 协议 ------------------------------------------------------------------


def test_fake_ingestor_satisfies_protocol():
    """结构化检查：实现核心契约的对象必须被认定为 Ingestor。"""
    assert isinstance(FakeIngestor(), Ingestor)


def test_fuyao_ingestor_satisfies_protocol():
    """参考实现本身也必须满足协议 —— 否则抽象是假的。"""
    from ingestors.fuyao.market import FuyaoMarketIngestor

    assert isinstance(FuyaoMarketIngestor(), Ingestor)


# --- 2. 契约校验 ---------------------------------------------------------------


def test_validate_rejects_missing_column():
    df = pd.DataFrame({"thscode": ["x"], "date": [pd.Timestamp("2024-01-01")]})
    with pytest.raises(ContractViolation, match="缺少契约列"):
        validate(df, "raw_kline_daily")


def test_validate_drops_extra_columns():
    df = FakeIngestor().fetch_daily_bars("600000.SH", "2024-01-01", "2024-12-31")
    df["some_vendor_specific_field"] = 1
    out = validate(df, "raw_kline_daily")
    assert "some_vendor_specific_field" not in out.columns
    assert list(out.columns) == [
        c for c in table_columns("raw_kline_daily") if c != "source_batch_id"
    ]


# --- 3. 端到端写入 -------------------------------------------------------------


@pytest.fixture
def writer(tmp_path):
    with DuckDbMarketWriter(tmp_path / "test.duckdb") as w:
        w.init_schema(SCHEMA_SQL)
        yield w


def test_write_and_read_back(writer):
    """Ingestor 产出 -> writer -> DuckDB -> 视图读出，全链路。"""
    ing = FakeIngestor()
    code = "600000.SH"

    syms = ing.list_symbols()
    bars = ing.fetch_daily_bars(code, "2024-01-01", "2024-12-31")
    factors = ing.fetch_adjust_factors(code, "2024-01-01", "2024-12-31")

    bid = new_batch_id("test")
    assert writer.write("dim_symbol", syms, batch_id=bid) == 3
    assert writer.write("raw_kline_daily", bars, batch_id=bid) == 400
    assert writer.write("calc_adjust_factor_daily", factors, batch_id=bid) == 400

    con = writer._con
    assert con.execute("SELECT count(*) FROM dim_symbol").fetchone()[0] == 3
    assert con.execute("SELECT count(*) FROM raw_kline_daily").fetchone()[0] == 400
    assert con.execute("SELECT count(*) FROM _import_batches").fetchone()[0] == 1

    # 视图可读 —— 契约的读取面确实建起来了
    n = con.execute("SELECT count(*) FROM v_daily_qfq").fetchone()[0]
    assert n > 0


def test_adjustment_identity_holds_after_roundtrip(writer):
    """v_daily_qfq 的定义是 close * forward_factor。

    写入再读出后该恒等式必须仍成立 —— 证明列顺序没错位、因子口径没串。
    """
    ing = FakeIngestor()
    code = "600000.SH"
    bid = new_batch_id("test")
    writer.write(
        "raw_kline_daily",
        ing.fetch_daily_bars(code, "2024-01-01", "2024-12-31"),
        batch_id=bid,
    )
    writer.write(
        "calc_adjust_factor_daily",
        ing.fetch_adjust_factors(code, "2024-01-01", "2024-12-31"),
        batch_id=bid,
    )

    con = writer._con
    raw = con.execute(
        "SELECT close FROM raw_kline_daily WHERE thscode=?", [code]
    ).fetchall()
    qfq = con.execute(
        "SELECT close FROM v_daily_qfq WHERE thscode=?", [code]
    ).fetchall()

    assert len(raw) == len(qfq) == 400
    factors = con.execute(
        "SELECT forward_factor FROM calc_adjust_factor_daily WHERE thscode=?", [code]
    ).fetchall()
    for (rc,), (qc,), (f,) in zip(raw, qfq, factors):
        assert qc == pytest.approx(rc * f, rel=1e-12)


def test_rewrite_is_idempotent(writer):
    """同一份数据写两次，行数不应翻倍（writer 按 thscode 先删后插）。"""
    ing = FakeIngestor()
    code = "600000.SH"
    bars = ing.fetch_daily_bars(code, "2024-01-01", "2024-12-31")
    writer.write("raw_kline_daily", bars, batch_id=new_batch_id("a"))
    writer.write("raw_kline_daily", bars, batch_id=new_batch_id("b"))
    assert writer._con.execute("SELECT count(*) FROM raw_kline_daily").fetchone()[0] == 400


# --- 4. 因子一致性校验 ---------------------------------------------------------


def test_check_factor_consistency_passes():
    ing = FakeIngestor()
    code = "600000.SH"
    report = check_factor_consistency(
        ing.fetch_daily_bars(code, "2024-01-01", "2024-12-31"),
        ing.fetch_adjust_factors(code, "2024-01-01", "2024-12-31"),
    )
    assert report["ok"] is True
    assert report["checked"] == 400


def test_check_factor_consistency_flags_empty_factors():
    """因子全空（未回填）时不能假装通过。"""
    bars = FakeIngestor().fetch_daily_bars("600000.SH", "2024-01-01", "2024-12-31")
    empty = bars[["thscode", "date"]].assign(forward_factor=float("nan"))
    report = check_factor_consistency(bars, empty)
    assert report["ok"] is False
