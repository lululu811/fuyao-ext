"""build_indicators.py — 全量构建 indicators.duckdb

支持 schema 迁移: --rebuild 删旧表重建.

警告: --rebuild 会 DROP 表并重算全部历史。给已有宽表加列请用
scripts/add_indicators.py,那是 config 驱动的差集回填路径。
"""

from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from indicator.compute import compute_one
from indicator.loader import list_thscodes, load_one
from paths import INDICATORS_CONFIG, INDICATORS_DB
from schema.indicators_schema import generate_create_table


def ensure_table(force: bool = False):
    """建表. force=True 会先删旧表,确保 schema 最新."""
    cfg = yaml.safe_load(INDICATORS_CONFIG.read_text())
    ddl = generate_create_table(cfg)
    con = duckdb.connect(str(INDICATORS_DB))
    try:
        if force:
            con.execute("DROP TABLE IF EXISTS v_indicators_daily")
        con.execute(ddl)
        con.commit()  # 关键: 持久化
    finally:
        con.close()


def build_one(thscode: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    df = load_one(thscode, start=start, end=end)
    return compute_one(df, thscode)


def run(
    thscodes: list[str],
    start: str | None = None,
    end: str | None = None,
    parquet_dir: Path | None = None,
):
    if parquet_dir is None:
        parquet_dir = Path(tempfile.mkdtemp(prefix="indicators_"))
    parquet_dir.mkdir(parents=True, exist_ok=True)

    t_total = time.time()
    t0 = time.time()
    written = []
    for i, code in enumerate(thscodes, 1):
        try:
            result = build_one(code, start=start, end=end)
            if result.empty:
                continue
            pq = parquet_dir / f"{code.replace('.', '_').replace('/', '_')}.parquet"
            result.to_parquet(pq, index=False)
            written.append((code, pq))
        except Exception as e:
            print(f"[err] {code}: {e}")

        if i % 50 == 0:
            elapsed = time.time() - t0
            print(f"  [{i}/{len(thscodes)}] {elapsed:.1f}s ({i/elapsed:.1f} codes/s)")

    print(f"\ncomputed {len(written)} codes in {time.time()-t_total:.1f}s")

    if written:
        print(f"\nloading {len(written)} parquet files into {INDICATORS_DB}...")
        con = duckdb.connect(str(INDICATORS_DB))
        try:
            codes_in_clause = ",".join(f"'{c[0]}'" for c in written)
            con.execute(f"DELETE FROM v_indicators_daily WHERE thscode IN ({codes_in_clause})")
            con.commit()

            pattern = str(parquet_dir / "*.parquet")
            con.execute(f"""
                INSERT INTO v_indicators_daily
                SELECT * FROM read_parquet('{pattern}')
            """)
            con.commit()
            count = con.execute("SELECT COUNT(*) FROM v_indicators_daily").fetchone()[0]
            print(f"  inserted; total rows now: {count:,}")
        finally:
            con.close()

        for _, pq in written:
            pq.unlink()
        try:
            parquet_dir.rmdir()
        except OSError:
            pass
        print(f"  cleaned up {parquet_dir}")

    print(f"\ntotal: {time.time()-t_total:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100, help="number of codes")
    parser.add_argument("--start", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--codes", type=str, default=None, help="comma-separated codes")
    parser.add_argument("--main-board", action="store_true", default=False,
                        help="only main board. default = all markets")
    parser.add_argument("--rebuild", action="store_true", default=False,
                        help="drop and recreate table (schema 变了必须用)")
    args = parser.parse_args()

    ensure_table(force=args.rebuild)

    if args.codes:
        codes = [c.strip() for c in args.codes.split(",")]
    else:
        all_codes = list_thscodes(main_board_only=args.main_board)
        codes = all_codes[:args.limit]
    print(f"building for {len(codes)} codes")
    if args.start or args.end:
        print(f"  date filter: {args.start} -> {args.end}")
    if args.rebuild:
        print("  REBUILD: dropped old table, new schema will be used")

    run(codes, start=args.start, end=args.end)
