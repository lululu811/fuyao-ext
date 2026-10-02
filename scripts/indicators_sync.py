"""indicators_sync.py — 增量构建 indicators.duckdb

策略:
  - 读 indicators.duckdb.MAX(date) 与 market.duckdb.MAX(date)
  - 找出 market 有但 indicators 没有的新日期
  - 重算这些日期 + lookback 天(保证长 lookback 指标稳定)
  - 删旧覆盖行 + INSERT OR REPLACE 新行(主键冲突时自动覆盖,避免 lookback 窗口内历史数据撞 PK)

用法:
  python scripts/indicators_sync.py
  python scripts/indicators_sync.py --lookback 75
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from multiprocessing import Pool

import duckdb
import pandas as pd  # noqa: F401  — 仅供 _worker_compute 的类型标注使用

from indicator.compute import compute_one
from indicator.loader import load_one
from paths import INDICATORS_CONFIG, INDICATORS_DB, MARKET_DB
from schema.indicators_schema import generate_create_table

# 增量重算窗口必须 ≥ 配置里最长的指标周期，否则长周期指标算不出来。
#
# 这里原来硬编码 75（自然日 ≈ 54 个交易日），而 indicators_config.yaml 声明的
# overlap.sma.params 是 [5,10,20,60,120,250]。54 < 250，于是 overlap_sma_60
# / _120 / _250 自 2026-08 起在增量路径上恒为 NULL —— 全市场 5,557 只票的
# 均线分析层整整两个月是空转的。
#
# 现在从配置里扫出真实最大周期，再按 A 股 ~0.72 的交易日/自然日比例换算，
# 并留 30% 余量。以后往 yaml 里加更长周期的指标，这里自动跟上，不会再漂移。
LOOKBACK_MIN_BARS = 60          # 下限，防止配置被清空时窗口过小
LOOKBACK_BUFFER_PCT = 1.3
TRADING_DAYS_PER_CALENDAR_DAY = 0.72


def _max_indicator_period(cfg: dict) -> int:
    """扫描配置里所有已启用指标的最大周期（根数）。"""
    def collect(x, out):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            out.append(int(x))
        elif isinstance(x, (list, tuple)):
            for y in x:
                collect(y, out)
        elif isinstance(x, dict):
            for y in x.values():
                collect(y, out)

    periods: list[int] = []
    for category, indicators in cfg.items():
        if category in ("metadata", "candles") or not isinstance(indicators, dict):
            continue
        for _iname, idef in indicators.items():
            if not isinstance(idef, dict) or not idef.get("enabled", False):
                continue
            collect(idef.get("params", []), periods)
    return max(periods) if periods else LOOKBACK_MIN_BARS


def _derive_lookback() -> int:
    import yaml
    cfg = yaml.safe_load(INDICATORS_CONFIG.read_text())
    bars = max(LOOKBACK_MIN_BARS, _max_indicator_period(cfg))
    calendar_days = int(bars / TRADING_DAYS_PER_CALENDAR_DAY * LOOKBACK_BUFFER_PCT)
    print(f"[lookback] 配置最大周期 {bars} bar → 窗口 {calendar_days} 自然日 "
          f"(约 {int(calendar_days * TRADING_DAYS_PER_CALENDAR_DAY)} 个交易日)")
    return calendar_days


DEFAULT_LOOKBACK = _derive_lookback()


def ensure_table(force: bool = False):
    """确保表存在,schema 最新."""
    cfg_path = INDICATORS_CONFIG
    import yaml
    cfg = yaml.safe_load(cfg_path.read_text())
    ddl = generate_create_table(cfg)
    con = duckdb.connect(str(INDICATORS_DB))
    try:
        if force:
            con.execute("DROP TABLE IF EXISTS v_indicators_daily")
        con.execute(ddl)
        con.commit()
    finally:
        con.close()


def get_date_range():
    """返回 (indicators_max_date, market_max_date)."""
    ind_max = None
    con = duckdb.connect(str(INDICATORS_DB), read_only=True)
    try:
        try:
            ind_max = con.execute(
                "SELECT MAX(date) FROM v_indicators_daily"
            ).fetchone()[0]
        except duckdb.CatalogException:
            pass
    finally:
        con.close()

    con = duckdb.connect(str(MARKET_DB), read_only=True)
    try:
        mkt_max = con.execute(
            "SELECT MAX(date) FROM v_daily"
        ).fetchone()[0]
    finally:
        con.close()
    return ind_max, mkt_max


def get_new_dates(ind_max, mkt_max):
    """返回 market 有但 indicators 没有的日期集合."""
    if ind_max is None or ind_max >= mkt_max:
        return set()
    con = duckdb.connect(str(MARKET_DB), read_only=True)
    try:
        rows = con.execute(f"""
            SELECT DISTINCT date FROM v_daily
            WHERE date > DATE '{ind_max}'
            ORDER BY date
        """).fetchall()
    finally:
        con.close()
    return {r[0] for r in rows}


def get_codes_with_new_data(new_dates):
    """返回有新数据的票号集合."""
    if not new_dates:
        return []
    con = duckdb.connect(str(MARKET_DB), read_only=True)
    try:
        min_date = min(new_dates)
        rows = con.execute(f"""
            SELECT DISTINCT thscode FROM v_daily
            WHERE date >= DATE '{min_date}'
            ORDER BY thscode
        """).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def _worker_compute(args: tuple) -> tuple[str, pd.DataFrame | None, str | None]:
    """多进程 worker: 加载行情 + 计算指标(只读,不写 DB)."""
    code, start, end = args
    try:
        df = load_one(code, start=start, end=end)
        if df.empty:
            return code, None, None
        result = compute_one(df, code)
        if result.empty:
            return code, None, None
        return code, result, None
    except Exception as e:
        return code, None, str(e)


def run(lookback: int = DEFAULT_LOOKBACK):
    """增量主流程."""
    ind_max, mkt_max = get_date_range()
    if ind_max is None:
        print("indicators.duckdb 是空,请用 build_indicators.py --rebuild --limit 6000 全量")
        return 1

    new_dates = get_new_dates(ind_max, mkt_max)
    if not new_dates:
        print(f"已最新 (indicators.max={ind_max} >= market.max={mkt_max}),无需更新")
        return 0

    min_new = min(new_dates)
    max_new = max(new_dates)
    start_date = min_new - datetime.timedelta(days=lookback)

    codes = get_codes_with_new_data(new_dates)
    if not codes:
        print(f"没有票需要重算 (新日期 {len(new_dates)} 个)")
        return 0

    print(f"增量: {len(new_dates)} 个新日期 ({min_new} ~ {max_new})")
    print(f"读 lookback={lookback} 天,从 {start_date} 开始")
    print(f"需重算 {len(codes)} 只票")

    # 1) 删除会被新数据覆盖的旧行
    con = duckdb.connect(str(INDICATORS_DB))
    try:
        codes_in = ",".join(f"'{c}'" for c in codes)
        con.execute(f"""
            DELETE FROM v_indicators_daily
            WHERE thscode IN ({codes_in})
              AND date >= DATE '{min_new}'
        """)
        con.commit()
    finally:
        con.close()

    # 2) 多进程并行计算 + 主进程写入 DB
    t0 = time.time()
    computed, failed = 0, 0
    n_workers = max(1, min(os.cpu_count() or 4, 10))
    work_items = [(code, str(start_date), str(mkt_max)) for code in codes]
    print(f"启动 {n_workers} 个 worker 并行计算...")

    con = duckdb.connect(str(INDICATORS_DB))
    try:
        with Pool(processes=n_workers) as pool:
            for i, (code, result, err) in enumerate(
                pool.imap_unordered(_worker_compute, work_items, chunksize=10), 1
            ):
                if err is not None:
                    print(f"[err] {code}: {err}")
                    failed += 1
                    continue
                if result is None:
                    continue
                try:
                    con.execute(f"""
                        DELETE FROM v_indicators_daily
                        WHERE thscode = '{code}' AND date >= DATE '{min_new}'
                    """)
                    con.register("df_temp", result)
                    con.execute("INSERT OR REPLACE INTO v_indicators_daily SELECT * FROM df_temp")
                    con.unregister("df_temp")
                    computed += 1
                except Exception as e:
                    print(f"[err] {code} DB write: {e}")
                    failed += 1

                if i % 50 == 0:
                    elapsed = time.time() - t0
                    print(f"  [{i}/{len(codes)}] {elapsed:.1f}s ({i/elapsed:.1f} codes/s, ok={computed}, fail={failed})")

        con.commit()
    finally:
        con.close()

    elapsed = time.time() - t0
    print(f"\n增量完成: {computed} 成功, {failed} 失败, {elapsed:.1f}s")

    # 3) 验证
    con = duckdb.connect(str(INDICATORS_DB), read_only=True)
    try:
        max_date = con.execute("SELECT MAX(date) FROM v_indicators_daily").fetchone()[0]
        n = con.execute("SELECT COUNT(*) FROM v_indicators_daily").fetchone()[0]
        c = con.execute("SELECT COUNT(DISTINCT thscode) FROM v_indicators_daily").fetchone()[0]
        print(f"  验证: max_date={max_date}, rows={n:,}, codes={c}")
    finally:
        con.close()

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK,
                        help=f"lookback window days (default {DEFAULT_LOOKBACK})")
    args = parser.parse_args()

    rc = run(lookback=args.lookback)
    sys.exit(rc)
