"""ingestors/base.py — 采集层协议

采集层只认**数据契约**，不认数据源。任何能产出契约所需字段的东西都是 Ingestor：
本项目自带的上游参考实现、tushare、akshare、自建 CSV 导入器等等。

核心契约（缺一不可）
--------------------
1. 证券标识        -> dim_symbol
2. 日线 OHLCV      -> raw_kline_daily
3. 复权因子        -> calc_adjust_factor_daily

可选能力
--------
除权除息事件、财务报表、指数、基金、期货、特色数据。实现与否不影响
Ingestor 满足核心契约。

设计要点
--------
Ingestor 只负责**产出契约形状的 DataFrame**，不碰数据库。
写入由 :class:`MarketWriter` 统一完成 —— 它按 ``schema/market.sql`` 的列定义
校验并落库。这样换数据源时只需写一个新的 Ingestor，writer 与下游全部不动。
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import pandas as pd

# --- 契约字段定义 -------------------------------------------------------------
# 目标表由 schema/market.sql 定义。这里列出 Ingestor 必须产出的列；
# source_batch_id / computed_at 等由 writer 填充，Ingestor 不必提供。

SYMBOL_COLUMNS = ["thscode", "ticker", "name", "exchange", "asset_type", "currency"]

KLINE_COLUMNS = [
    "thscode",
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "turnover",
    "currency",
    "interval",
    "adjusted",
]

FACTOR_COLUMNS = ["thscode", "date", "forward_factor", "backward_factor"]

ADJUSTMENT_EVENT_COLUMNS = [
    "thscode",
    "ticker",
    "ex_date",
    "dividend_per_share",
    "per_share_bonus",
    "allotment_ratio",
    "allotment_price",
    "currency",
]

#: 核心契约的表名 -> Ingestor 必须产出的列
CORE_CONTRACT: dict[str, list[str]] = {
    "dim_symbol": SYMBOL_COLUMNS,
    "raw_kline_daily": KLINE_COLUMNS,
    "calc_adjust_factor_daily": FACTOR_COLUMNS,
}


class ContractViolation(ValueError):
    """Ingestor 产出的 DataFrame 不满足数据契约。"""


@dataclass(frozen=True)
class IngestorInfo:
    """数据源自述。用于生成文档，也供使用者判断该 Ingestor 是否适合自己的数据源。"""

    name: str
    homepage: str
    credential_env: str
    credential_help: str
    notes: str = ""
    supports: tuple[str, ...] = field(default=())

    def as_rows(self) -> list[tuple[str, str]]:
        return [
            ("名称", self.name),
            ("官网", self.homepage),
            ("凭据环境变量", f"`{self.credential_env}`"),
            ("凭据申请", self.credential_help),
            ("支持的可选能力", ", ".join(self.supports) or "（仅核心契约）"),
            ("备注", self.notes or "—"),
        ]


@runtime_checkable
class Ingestor(Protocol):
    """采集器协议。

    实现者只需提供这四个方法。全部返回**契约形状**的 DataFrame：
    列名与 :data:`CORE_CONTRACT` 一致，日期列为 ``datetime64`` 或 ``date``，
    数值列为可空浮点。不必关心 batch id、落库、事务。

    实现者应保证：同一个 ``(thscode, start, end)`` 重复调用结果幂等。
    """

    def describe(self) -> IngestorInfo:
        """自述：需要什么凭据、支持什么、有什么坑。"""
        ...

    def list_symbols(self) -> pd.DataFrame:
        """产出 dim_symbol 的列：thscode, ticker, name, exchange, asset_type, currency"""
        ...

    def fetch_daily_bars(
        self, thscode: str, start: str, end: str
    ) -> pd.DataFrame:
        """产出 raw_kline_daily 的列。

        必须是**未复权**原始价（对应上游的 ``adjust=none``）——
        复权由因子表承担，不要在价格里预先复权，否则因子无从校验。

        ``start`` / ``end`` 为 ``YYYY-MM-DD``。
        """
        ...

    def fetch_adjust_factors(
        self, thscode: str, start: str, end: str
    ) -> pd.DataFrame:
        """产出 calc_adjust_factor_daily 的列：thscode, date, forward_factor, backward_factor

        因子应与本 Ingestor 的未复权价格口径一致，即
        ``adjusted_close = close * forward_factor`` 必须成立。
        """
        ...


def validate(df: pd.DataFrame, table: str, *, allow_empty: bool = True) -> pd.DataFrame:
    """校验 DataFrame 满足契约，返回规范化副本。

    缺列抛 :class:`ContractViolation`；多出的列被丢弃（writer 会按
    ``schema/market.sql`` 的列顺序写入，多余列会造成错位）。
    """
    required = CORE_CONTRACT[table] if table in CORE_CONTRACT else _contract_for(table)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ContractViolation(f"{table}: 缺少契约列 {missing}（实际 {list(df.columns)}）")
    if df.empty and not allow_empty:
        raise ContractViolation(f"{table}: 返回空表")
    return df.loc[:, required].copy()


def _contract_for(table: str) -> list[str]:
    return ADJUSTMENT_EVENT_COLUMNS


class MarketWriter(abc.ABC):
    """把 Ingestor 产出落库。实现方负责具体存储细节。"""

    @abc.abstractmethod
    def write(self, table: str, df: pd.DataFrame, *, batch_id: str) -> int:
        """写入一张表，返回写入行数。"""


def check_factor_consistency(
    bars: pd.DataFrame, factors: pd.DataFrame, *, tol: float = 1e-6
) -> dict[str, Any]:
    """校验复权因子与未复权价格自洽。

    只用 forward 因子与 close 做一致性检查：因子表若为全 1（未回填）
    或口径错乱，这里会立刻暴露。
    """
    if bars.empty or factors.empty:
        return {"checked": 0, "ok": True, "reason": "空表，跳过"}

    m = bars[["thscode", "date", "close"]].merge(
        factors[["thscode", "date", "forward_factor"]],
        on=["thscode", "date"],
        how="inner",
    )
    m = m[m["close"].notna() & m["forward_factor"].notna() & (m["close"] != 0)]
    if m.empty:
        return {"checked": 0, "ok": False, "reason": "价格与因子无法按主键对齐"}

    implied = m["forward_factor"]
    degenerate = int((implied == 1.0).sum())
    return {
        "checked": int(len(m)),
        "ok": bool(implied.between(1e-6, 1e6).all()),
        "factor_equals_1": degenerate,
        "min": float(implied.min()),
        "max": float(implied.max()),
    }
