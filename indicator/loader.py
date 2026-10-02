"""loader.py — 从 duckdb 读日线数据,标准化成指标引擎期望的格式

输入数据库:  paths.MARKET_DB（默认 ~/.hithink-finance/market.duckdb）
             v_daily_qfq(thscode, date, open, high, low, close, volume)
输出:        DataFrame,DatetimeIndex(date),columns=[open, high, low, close, volume]
             (单只票) 或 dict[thscode -> DataFrame] (多只票批量)

价基说明（重要）
这里读 **`v_daily_qfq`（前复权）**，不是 `v_daily`（未复权）。
约定：个股分析一律用前复权价，`v_daily` 只用于查除权事件。

之前这里读的是 `v_daily`，而下游读的是 `v_daily_qfq` —— 指标算在未复权价上、
却和前复权价比较。实测最大相对差：`momentum_rsi_14` 21.7%、`volatility_atr_14` 14.8%、
`overlap_sma_20` 7.8%；全库 329 万根 K 线的复权因子偏离 >10%。
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from paths import MARKET_DB

DEFAULT_DB = MARKET_DB

# 价基来源。改这里就能在"前复权"和"未复权"之间切换。
PRICE_VIEW = "v_daily_qfq"


def _standardize(df: pd.DataFrame) -> pd.DataFrame:
    """统一列名小写,设 date 为 index,只保留 OHLCV."""
    df = df.rename(columns=str.lower)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")
    keep = ["open", "high", "low", "close", "volume"]
    return df[[c for c in keep if c in df.columns]].sort_index()


def load_one(
    thscode: str,
    db_path: str | Path = DEFAULT_DB,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """读单只票的日线.

    Args:
        thscode: 形如 '601398.SH'
        start/end: ISO 日期字符串,None 表示不限
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        sql = f"""
            SELECT date, open, high, low, close, volume
            FROM {PRICE_VIEW} WHERE thscode = ?
        """
        params = [thscode]
        if start:
            sql += " AND date >= ?"
            params.append(start)
        if end:
            sql += " AND date <= ?"
            params.append(end)
        sql += " ORDER BY date"
        df = con.execute(sql, params).fetchdf()
    finally:
        con.close()
    if df.empty:
        return df
    return _standardize(df)


def load_many(
    thscodes: list[str],
    db_path: str | Path = DEFAULT_DB,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, pd.DataFrame]:
    """读多只票的日线,返回 {thscode: DataFrame}.

    用一次 SQL 把所有 thscode 的数据拉回来,在 Python 里 groupby 切分,
    避免 N 次单查的开销。
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        placeholders = ",".join(["?"] * len(thscodes))
        sql = f"""
            SELECT thscode, date, open, high, low, close, volume
            FROM {PRICE_VIEW} WHERE thscode IN ({placeholders})
        """
        params = list(thscodes)
        if start:
            sql += " AND date >= ?"
            params.append(start)
        if end:
            sql += " AND date <= ?"
            params.append(end)
        sql += " ORDER BY thscode, date"
        df = con.execute(sql, params).fetchdf()
    finally:
        con.close()
    if df.empty:
        return {}
    df["date"] = pd.to_datetime(df["date"])
    out: dict[str, pd.DataFrame] = {}
    for code, sub in df.groupby("thscode"):
        sub = sub.drop(columns=["thscode"]).set_index("date")
        keep = ["open", "high", "low", "close", "volume"]
        sub = sub[[c for c in keep if c in sub.columns]].sort_index()
        out[code] = sub
    return out


def list_thscodes(
    db_path: str | Path = DEFAULT_DB,
    main_board_only: bool = True,
) -> list[str]:
    """列出所有 thscode (默认只主板 60xxxx.SH / 00xxxx.SZ).

    main_board_only=False 包含科创板(688)、创业板(300/301) 等.
    """
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        if main_board_only:
            sql = f"""
                SELECT DISTINCT thscode FROM {PRICE_VIEW}
                WHERE (thscode LIKE '60%.SH' OR thscode LIKE '00%.SZ')
                ORDER BY thscode
            """
        else:
            sql = f"SELECT DISTINCT thscode FROM {PRICE_VIEW} ORDER BY thscode"
        rows = con.execute(sql).fetchall()
        return [r[0] for r in rows]
    finally:
        con.close()


if __name__ == "__main__":
    # 简单验证
    df = load_one("601398.SH")
    print(f"601398.SH: {len(df)} rows, {df.index.min().date()} -> {df.index.max().date()}")
    codes = list_thscodes(main_board_only=True)
    print(f"main board codes: {len(codes)}, first 5: {codes[:5]}")
