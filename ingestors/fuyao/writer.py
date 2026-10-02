"""ingestors/fuyao/writer.py — 把 Ingestor 产出落进 DuckDB

按 ``schema/market.sql`` 的列定义写入，不关心数据来自哪里 ——
换数据源时本文件无需改动。
"""

from __future__ import annotations

import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd

from paths import MARKET_DB
from schema.ddl import TARGET_COLUMNS

#: 由 writer 填充、不要求 Ingestor 提供的列。
#:
#: Ingestor 只负责产出契约要求的业务列；溯源与时间戳是写入方的职责。
#: 与 ingestors/base.py 的 CORE_CONTRACT 约定一致。
WRITER_MANAGED: dict[str, dict[str, str]] = {
    "dim_symbol": {"source_batch_id": "batch_id", "updated_at": "now"},
    "raw_kline_daily": {"source_batch_id": "batch_id"},
    "raw_adjustment_events": {"source_batch_id": "batch_id"},
    "calc_adjust_factor_daily": {
        "source_event_batch_id": "batch_id",
        "factor_version": "literal:fuyao-ratio-v1",
        "calculated_at": "now",
    },
}


def new_batch_id(kind: str) -> str:
    """批次号。形如 ``fuyao-symbols-20261002T094500Z-1f54ec18``。"""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"fuyao-{kind}-{ts}-{uuid.uuid4().hex[:8]}"


class DuckDbMarketWriter:
    """DuckDB 实现的市场域 writer。"""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = str(db_path or MARKET_DB)

    def __enter__(self) -> DuckDbMarketWriter:
        self._con = duckdb.connect(self.db_path)
        return self

    def __exit__(self, *exc: object) -> None:
        self._con.close()

    def init_schema(self, ddl: str | None = None) -> None:
        """建表。默认读取 schema/market.sql。"""
        if ddl is None:
            ddl = (Path(__file__).resolve().parent.parent.parent / "schema" / "market.sql").read_text()
        self._con.execute(ddl)

    def write(self, table: str, df: pd.DataFrame, *, batch_id: str) -> int:
        """写入一张表并登记批次。返回写入行数。

        Ingestor 只需提供业务列；``source_batch_id`` 等溯源列由本方法补齐。
        """
        cols = TARGET_COLUMNS[table]
        managed = WRITER_MANAGED.get(table, {})
        incoming = df.copy()

        for col, rule in managed.items():
            if col in incoming.columns and not incoming[col].isna().all():
                continue  # Ingestor 显式给了值，尊重它
            if rule == "batch_id":
                incoming[col] = batch_id
            elif rule == "now":
                incoming[col] = pd.Timestamp.now("UTC").tz_localize(None)
            elif rule.startswith("literal:"):
                incoming[col] = rule.split(":", 1)[1]

        missing = [c for c in cols if c not in incoming.columns]
        if missing:
            raise ValueError(
                f"{table}: 缺少列 {missing}。"
                f"契约要求 {cols}，writer 可自动补齐的列：{sorted(managed)}"
            )

        con = self._con
        con.register("_incoming", incoming.loc[:, cols])
        quoted = ", ".join(f'"{c}"' for c in cols)
        # 按 thscode 覆盖写：先删该批标的的旧行，再整表插入。
        # 契约层已声明主键，但 DuckDB 不强制约束，覆盖写由这一步保证。
        con.execute(f"DELETE FROM {table} WHERE thscode IN (SELECT DISTINCT thscode FROM _incoming)")
        con.execute(f"INSERT INTO {table} ({quoted}) SELECT {quoted} FROM _incoming")
        con.unregister("_incoming")

        self._record_batch(batch_id, table, len(incoming))
        return len(incoming)

    def _record_batch(self, batch_id: str, kind: str, row_count: int) -> None:
        con = self._con
        if self._has_table("_import_batches"):
            con.execute(
                "INSERT INTO _import_batches (batch_id, source, kind, started_at, finished_at, row_count) "
                "VALUES (?, 'rest', ?, now(), now(), ?) "
                "ON CONFLICT (batch_id) DO UPDATE SET finished_at=now(), row_count=excluded.row_count",
                [batch_id, kind, row_count],
            )
        else:
            con.execute(
                "INSERT INTO _import_batches (batch_id, source, kind, started_at, finished_at, row_count) "
                "VALUES (?, 'rest', ?, now(), now(), ?)",
                [batch_id, kind, row_count],
            )

    def _has_table(self, name: str) -> bool:
        row = self._con.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [name]
        ).fetchone()
        return bool(row and row[0])


__all__ = ["DuckDbMarketWriter", "new_batch_id", "closing"]
