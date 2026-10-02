"""ingestors/fuyao/market.py — 行情数据域的 Ingestor 实现

这是本项目**自行编写**的行情采集实现，产出 schema/market.sql 定义的：

    dim_symbol                证券目录
    raw_kline_daily           未复权日线 OHLCV
    raw_adjustment_events     除权除息事件
    calc_adjust_factor_daily  前/后复权因子

复权因子怎么来的
----------------
不重算除权除息数学。上游同一接口支持 ``adjust=none|forward|backward`` 三种价格，
而 ``v_daily_qfq`` 的定义是 ``close * forward_factor = 前复权收盘价``，
所以因子就是**两种价格之比**：

    forward_factor  = 前复权收盘价 / 未复权收盘价
    backward_factor = 后复权收盘价 / 未复权收盘价

这样做的好处是因子与上游的复权口径**严格一致** —— 若自己实现除权除息
公式，任何一处假设偏差都会让因子与实际价格对不上，而用比值则不可能对不上。

用法
----
    export HITHINK_FINANCE_API_KEY=...
    python -m ingestors.fuyao.market --symbols
    python -m ingestors.fuyao.market --codes 600519.SH,000001.SZ
    python -m ingestors.fuyao.market --all --start 2016-09-12
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from ingestors.base import (
    ADJUSTMENT_EVENT_COLUMNS,
    FACTOR_COLUMNS,
    KLINE_COLUMNS,
    SYMBOL_COLUMNS,
    IngestorInfo,
    check_factor_consistency,
    validate,
)
from ingestors.fuyao.client import FuyaoClient, _ms
from ingestors.fuyao.writer import DuckDbMarketWriter, new_batch_id

# 上游单次 K 线请求窗口上限为 10 年
MAX_WINDOW_DAYS = 3650


class FuyaoMarketIngestor:
    """行情 Ingestor。实现 :class:`ingestors.base.Ingestor` 的核心契约。"""

    def __init__(self, client: FuyaoClient | None = None):
        self._client = client
        self._symbols: pd.DataFrame | None = None

    @property
    def client(self) -> FuyaoClient:
        if self._client is None:
            self._client = FuyaoClient()
        return self._client

    # --- Ingestor 协议 --------------------------------------------------------

    def describe(self) -> IngestorInfo:
        return IngestorInfo(
            name="同花顺 hithink-finance",
            homepage="https://fuyao.aicubes.cn/",
            credential_env="HITHINK_FINANCE_API_KEY",
            credential_help="https://fuyao.aicubes.cn/admin/",
            notes=(
                "本实现为 fuyao-ext 自行编写，调用其公开 REST API，"
                "不含上游任何代码。单次 K 线请求窗口上限 10 年，"
                "超过会返回 code=1003，因此按 10 年切片。"
            ),
            supports=("raw_adjustment_events",),
        )

    def list_symbols(self, *, asset_type: str = "a-share") -> pd.DataFrame:
        """产出 dim_symbol 的列。"""
        if self._symbols is not None:
            return self._symbols.copy()

        rows = self.client.list_tickers(asset_type=asset_type)
        if not rows:
            return pd.DataFrame(columns=SYMBOL_COLUMNS)

        df = pd.DataFrame(rows)
        for col, default in (
            ("thscode", None), ("ticker", None), ("name", None),
            ("exchange", None), ("asset_type", None), ("currency", "CNY"),
        ):
            if col not in df.columns:
                df[col] = default

        self._symbols = validate(df, "dim_symbol")
        return self._symbols.copy()

    def fetch_daily_bars(self, thscode: str, start: str, end: str) -> pd.DataFrame:
        """产出 raw_kline_daily 的列，价格为**未复权**口径。"""
        records: list[dict] = []
        for w_start, w_end in _windows(start, end):
            records.extend(self.client.daily_bars(thscode, _ms(w_start), _ms(w_end), adjust="none"))

        if not records:
            return pd.DataFrame(columns=KLINE_COLUMNS)

        df = pd.DataFrame(records).rename(
            columns={
                "date_ms": "date",
                "open_price": "open",
                "high_price": "high",
                "low_price": "low",
                "close_price": "close",
            }
        )
        df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True).dt.tz_localize(None)
        df["thscode"] = thscode
        df["interval"] = "1d"
        df["adjusted"] = "none"
        df["currency"] = "CNY"

        return validate(df, "raw_kline_daily")

    def fetch_adjust_factors(self, thscode: str, start: str, end: str) -> pd.DataFrame:
        """由三种价格口径之比推导复权因子。"""
        raw = self.fetch_daily_bars(thscode, start, end)
        if raw.empty:
            return pd.DataFrame(columns=FACTOR_COLUMNS)

        fwd_rows: list[dict] = []
        bwd_rows: list[dict] = []
        for w_start, w_end in _windows(start, end):
            s, e = _ms(w_start), _ms(w_end)
            fwd_rows.extend(self.client.daily_bars(thscode, s, e, adjust="forward"))
            bwd_rows.extend(self.client.daily_bars(thscode, s, e, adjust="backward"))

        fwd = _close_map(fwd_rows)
        bwd = _close_map(bwd_rows)

        out = raw[["thscode", "date", "close"]].copy()
        out["forward_factor"] = [
            _safe_ratio(fwd.get(d), c) for d, c in zip(out["date"], out["close"])
        ]
        out["backward_factor"] = [
            _safe_ratio(bwd.get(d), c) for d, c in zip(out["date"], out["close"])
        ]
        # close 为 0 或缺失时因子无定义，回落为 1.0（等价于不复权）
        out["forward_factor"] = out["forward_factor"].fillna(1.0)
        out["backward_factor"] = out["backward_factor"].fillna(1.0)

        return validate(out, "calc_adjust_factor_daily")

    def fetch_adjustment_events(self, thscode: str, start: str, end: str) -> pd.DataFrame:
        """产出 raw_adjustment_events 的列（可选能力）。"""
        rows = self.client.adjustment_events(thscode, start, end)
        if not rows:
            return pd.DataFrame(columns=ADJUSTMENT_EVENT_COLUMNS)

        df = pd.DataFrame(rows).rename(columns={"ex_date_ms": "ex_date"})
        df["ex_date"] = pd.to_datetime(df["ex_date"], unit="ms", utc=True).dt.tz_localize(None)
        df["thscode"] = thscode
        df["currency"] = "CNY"
        for col in ("dividend_per_share", "per_share_bonus", "allotment_ratio", "allotment_price"):
            if col not in df.columns:
                df[col] = None
        return validate(df, "raw_adjustment_events", allow_empty=False)

    def list_thscodes(self) -> list[str]:
        return self.list_symbols()["thscode"].tolist()


# --- 辅助 --------------------------------------------------------------------


def _windows(start: str, end: str) -> list[tuple[str, str]]:
    """把 [start, end] 切成不超过 MAX_WINDOW_DAYS 的窗口（上游 10 年上限）。"""
    s = datetime.strptime(start, "%Y-%m-%d").date()
    e = datetime.strptime(end, "%Y-%m-%d").date()
    out: list[tuple[str, str]] = []
    cur = s
    while cur <= e:
        stop = min(cur + timedelta(days=MAX_WINDOW_DAYS), e)
        out.append((cur.isoformat(), stop.isoformat()))
        cur = stop + timedelta(days=1)
    return out


def _close_map(rows: list[dict]) -> dict[Any, float]:
    return {
        r["date_ms"]: float(r["close_price"])
        for r in rows
        if r.get("date_ms") is not None and r.get("close_price") is not None
    }


def _safe_ratio(adjusted: float | None, raw: float | None) -> float | None:
    if adjusted is None or raw in (None, 0):
        return None
    return adjusted / raw


# --- CLI ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="同花顺 hithink-finance 行情 Ingestor")
    ap.add_argument("--symbols", action="store_true", help="只拉取证券目录")
    ap.add_argument("--codes", help="逗号分隔的 thscode")
    ap.add_argument("--all", action="store_true", help="全部 A 股标的")
    ap.add_argument("--start", default="2016-09-12")
    ap.add_argument("--end", help="默认今天")
    ap.add_argument("--db", help="目标 DuckDB 路径，默认 $FUYAO_HOME/market.duckdb")
    ap.add_argument("--dry-run", action="store_true", help="只打印统计，不落库")
    args = ap.parse_args(argv)

    end = args.end or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ing = FuyaoMarketIngestor()

    if args.symbols:
        syms = ing.list_symbols()
        print(f"证券目录: {len(syms)} 条")
        if not args.dry_run:
            with DuckDbMarketWriter(args.db) as w:
                w.init_schema()
                n = w.write("dim_symbol", syms, batch_id=new_batch_id("symbols"))
            print(f"已写入 dim_symbol: {n} 行")
        return 0

    codes = (
        [c.strip() for c in args.codes.split(",") if c.strip()]
        if args.codes
        else (ing.list_thscodes() if args.all else [])
    )
    if not codes:
        ap.error("需指定 --codes 或 --all（或用 --symbols 只拉目录）")

    writer = None if args.dry_run else DuckDbMarketWriter(args.db)
    if writer is not None:
        writer.init_schema()

    total = 0
    degraded = 0
    try:
        for i, code in enumerate(codes, 1):
            bars = ing.fetch_daily_bars(code, args.start, end)
            factors = ing.fetch_adjust_factors(code, args.start, end)
            report = check_factor_consistency(bars, factors)
            if not report["ok"]:
                degraded += 1
            total += len(bars)
            print(
                f"[{i}/{len(codes)}] {code}  bars={len(bars):5}  factors={len(factors):5}  "
                f"factor=[{report.get('min', 0):.4f}, {report.get('max', 0):.4f}]  "
                f"ok={report['ok']}"
            )
            if writer is not None:
                bid = new_batch_id("market")
                writer.write("raw_kline_daily", bars, batch_id=bid)
                writer.write("calc_adjust_factor_daily", factors, batch_id=bid)
    finally:
        if writer is not None:
            writer.__exit__(None, None, None)

    verb = "（dry-run，未落库）" if args.dry_run else ""
    print(f"合计 {total} 行日线{verb}")
    if degraded:
        print(f"⚠ {degraded} 只标的的因子一致性校验未通过", file=sys.stderr)
        return 10
    return 0


if __name__ == "__main__":
    sys.exit(main())
