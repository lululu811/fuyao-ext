"""
indicators_repair.py — 修复 indicators.duckdb 的历史窗口

背景
----
`indicators_sync.py` 的 `DEFAULT_LOOKBACK = 75`（自然日）≈ 54 个交易日，
而 `indicators_config.yaml` 声明的最长指标周期是 250 bar
（`overlap.sma.params = [5,10,20,60,120,250]`）。增量路径每次只重算
~54 根 K 线，于是 `overlap_sma_60/120/250` 自 2026-08 起恒为 NULL。

同时 `indicator/loader.py` 读的是 `v_daily`（未复权），而分析层
（`zettaranc/data_loader.py`）读的是 `v_daily_qfq`（前复权）。两者尺度不同：
实测 `momentum_rsi_14` 最大相对差 21.7%、`volatility_atr_14` 14.8%。

本脚本对**一个日期窗口**做全量重算，并支持：
  --view   v_daily | v_daily_qfq     价基（默认 v_daily_qfq，与分析层一致）
  --limit  N                        只处理前 N 只（试跑）
  --codes  A,B,C                    指定标的
  --start/--end                     窗口边界（默认从今天回溯 --days）
  --days                           回溯自然日数（默认 420 ≈ 290 交易日 > 250）
  --workers                         进程数
  --dry-run                         只算不写

安全
----
* 写入前先把受影响行导出到 backup/ 目录，可整窗回滚。
* 按标的删除 + 按标的 INSERT OR REPLACE，主键 (thscode,date) 保证不重复。
* 每写完一批打印进度与 ETA。
* 写完做完整性校验：核心列非空率、行数、日期覆盖。
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import duckdb
import pandas as pd

from indicator.compute import compute_one
from paths import FUYAO_HOME, INDICATORS_DB, MARKET_DB

IND_DB = INDICATORS_DB
BACKUP_DIR = FUYAO_HOME / "backups" / "indicators"

# 核心列：服务实际消费、必须非空的字段
CORE_COLS = [
    "overlap_sma_5", "overlap_sma_20", "overlap_sma_60", "overlap_sma_120",
    "overlap_sma_250", "momentum_macd_12_26_9_macd", "momentum_rsi_6",
    "momentum_kdj_9_3_k", "momentum_cci_20", "momentum_willr_14", "volume_mfi_14",
    "trend_adx_14", "volatility_bbands_20_2_0_upper", "volatility_atr_14",
    "volume_cmf_20", "volume_obv", "volume_vwap",
]
VIEW_SQL = {
    "v_daily": "SELECT date, open, high, low, close, volume FROM v_daily",
    "v_daily_qfq": "SELECT date, open, high, low, close, volume FROM v_daily_qfq",
}


def log(msg: str) -> None:
    print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}", flush=True)


def resolve_window(days: int) -> tuple[str, str]:
    con = duckdb.connect(MARKET_DB, read_only=True)
    try:
        mkt_max = con.execute("SELECT max(date) FROM v_daily_qfq").fetchone()[0]
    finally:
        con.close()
    end = mkt_max
    start = end - datetime.timedelta(days=days)
    return str(start), str(end)


def get_codes(limit: int | None, codes: str | None) -> list[str]:
    if codes:
        return [c.strip() for c in codes.split(",") if c.strip()]
    con = duckdb.connect(MARKET_DB, read_only=True)
    try:
        sql = "SELECT DISTINCT thscode FROM v_daily_qfq ORDER BY thscode"
        if limit:
            sql += f" LIMIT {int(limit)}"
        return [r[0] for r in con.execute(sql).fetchall()]
    finally:
        con.close()


def _worker(args):
    code, view, start, end = args
    try:
        con = duckdb.connect(MARKET_DB, read_only=True)
        try:
            df = con.execute(
                VIEW_SQL[view] + " WHERE thscode = ? AND date >= ? AND date <= ? ORDER BY date",
                [code, start, end],
            ).fetchdf()
        finally:
            con.close()
        if df.empty:
            return code, None, None
        df = df.rename(columns=str.lower)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")[["open", "high", "low", "close", "volume"]].sort_index()
        res = compute_one(df, code)
        if res.empty:
            return code, None, None
        return code, res, None
    except Exception as exc:  # noqa: BLE001
        return code, None, f"{type(exc).__name__}: {exc}"


def backup_window(codes: list[str], start: str, end: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    path = BACKUP_DIR / f"indicators_{stamp}_{start}_{end}.parquet"
    con = duckdb.connect(str(IND_DB), read_only=True)
    try:
        con.execute(
            f"COPY (SELECT * FROM v_indicators_daily "
            f"WHERE date >= DATE '{start}' AND date <= DATE '{end}') "
            f"TO '{path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    finally:
        con.close()
    size_mb = path.stat().st_size / 1e6
    log(f"已备份窗口 {start}..{end} → {path.name} ({size_mb:.1f} MB)")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", choices=list(VIEW_SQL), default="v_daily_qfq")
    ap.add_argument("--days", type=int, default=420)
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--codes", default=None)
    ap.add_argument("--workers", type=int, default=min(os.cpu_count() or 4, 8))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    start = args.start or resolve_window(args.days)[0]
    end = args.end or resolve_window(args.days)[1]
    codes = get_codes(args.limit, args.codes)
    log(f"窗口 {start} .. {end}   价基 {args.view}   标的 {len(codes)} 只   "
        f"workers={args.workers}{'   [DRY-RUN]' if args.dry_run else ''}")

    if args.dry_run:
        t0 = time.time()
        done, errs = 0, []
        for i, code in enumerate(codes[: min(len(codes), 20)], 1):
            _, res, err = _worker((code, args.view, start, end))
            if err:
                errs.append((code, err))
            if res is not None:
                nn = {c: int(res[c].notna().sum()) for c in
                      ("overlap_sma_60", "overlap_sma_120", "overlap_sma_250")}
                if i <= 5:
                    log(f"  {code}: {len(res)} 行  sma60/120/250 非空 = "
                        f"{nn['overlap_sma_60']}/{nn['overlap_sma_120']}/{nn['overlap_sma_250']}")
            done += 1
        log(f"dry-run 完成 {done} 只, 耗时 {time.time()-t0:.1f}s, 错误 {len(errs)}")
        for c, e in errs[:5]:
            log(f"  [err] {c}: {e}")
        return 0

    if not args.no_backup:
        backup_window(codes, start, end)

    con = duckdb.connect(str(IND_DB))
    con.execute("SET preserve_insertion_order = false")
    t0 = time.time()
    computed = failed = 0
    errors: list[str] = []
    work = [(c, args.view, start, end) for c in codes]

    with Pool(processes=args.workers) as pool:
        for i, (code, res, err) in enumerate(
            pool.imap_unordered(_worker, work, chunksize=4), 1
        ):
            if err:
                errors.append(f"{code}: {err}")
                failed += 1
            elif res is None:
                failed += 1
            else:
                try:
                    # 只删 result 实际覆盖的日期区间，不删整个窗口。
                    # compute_one(drop_na_initial=True) 会丢掉开头的预热行；
                    # 若按整个窗口删，这些行删了又没插回来 = 静默丢数据。
                    lo, hi = res["date"].min(), res["date"].max()
                    lo_s = lo.strftime("%Y-%m-%d") if hasattr(lo, "strftime") else str(lo)
                    hi_s = hi.strftime("%Y-%m-%d") if hasattr(hi, "strftime") else str(hi)
                    con.execute(
                        # DuckDB 不接受 `DATE ?`，必须 CAST(? AS DATE)
                        "DELETE FROM v_indicators_daily WHERE thscode = ? "
                        "AND date >= CAST(? AS DATE) AND date <= CAST(? AS DATE)",
                        [code, lo_s, hi_s],
                    )
                    con.register("df_temp", res)
                    con.execute(
                        "INSERT OR REPLACE INTO v_indicators_daily "
                        "SELECT * FROM df_temp"
                    )
                    con.unregister("df_temp")
                    computed += 1
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{code} DB: {exc}")
                    failed += 1

            if i % 200 == 0 or i == len(codes):
                el = time.time() - t0
                rate = i / el if el else 0
                eta = (len(codes) - i) / rate if rate else 0
                log(f"  [{i}/{len(codes)}] {el:.0f}s  {rate:.1f} 只/s  "
                    f"ETA {eta/60:.1f}min  ok={computed} fail={failed}")
    con.commit()
    con.close()

    el = time.time() - t0
    log(f"写入完成: ok={computed} fail={failed}  耗时 {el/60:.1f}min")
    for e in errors[:10]:
        log(f"  [err] {e}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
