"""add_indicators.py — 把 indicators_config.yaml 里新增/缺失的指标列补进现有宽表

取代 add_zettaranc_columns.py(那个把 6 列写死了)。本脚本是 config 驱动的:

  1. 从 config 推导「应该存在哪些列」(schema.expand_columns + expand_cdl_columns)
  2. 读表里实际有哪些列
  3. 差集 = 待新增 → ALTER TABLE ADD COLUMN
  4. 只算这些新列(不重算已有 231 列),批量 upsert

第 4 步是关键:indicator.compute_one 跑全量 ~244 列占 99% 耗时,
只算差集那几列通常快 1-2 个数量级。这是 2026-09-22 给 indicators.duckdb
(16GB / 5572 只 × 10 年)加列的唯一可行路径 —— 绝不要用 build_indicators.py
--rebuild,那会 drop 表重算 10 年。

用法:
    python scripts/add_indicators.py --dry-run            # 只看会加什么,不写
    python scripts/add_indicators.py --codes 600519.SH,000001.SZ
    python scripts/add_indicators.py                      # 全量回填
    python scripts/add_indicators.py --only ichimoku,brar  # 只处理指定指标

退出码: 0 干净 / 10 降级(有票算失败) / 2 参数或环境错误
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import timedelta

import duckdb
import pandas as pd

from indicator.adapter_pandas_ta import calc_indicator as pandas_ta_calc
from indicator.adapter_talib import calc_indicator as talib_calc
from indicator.compute import _load_config, _make_col_prefix, _normalize_params, _pick_backend
from indicator.loader import load_many
from paths import INDICATORS_DB
from schema.indicators_schema import expand_cdl_columns, expand_columns

TABLE = "v_indicators_daily"


# ---------------------------------------------------------------------------
# config → 计算规格
# ---------------------------------------------------------------------------

def build_specs(cfg: dict) -> dict[str, dict]:
    """遍历 config,返回 {列名: 规格}。

    规格 = {category, iname, params, outputs, backend_cfg, native_lib, col_prefix}
    同一指标的多个 param/多输出各自独立成条目。
    """
    specs: dict[str, dict] = {}
    for category, indicators in cfg.items():
        if category in {"metadata", "candles"} or not isinstance(indicators, dict):
            continue
        for iname, idef in indicators.items():
            if iname == "all_cdl" or not isinstance(idef, dict):
                continue
            if not idef.get("enabled", False):
                continue
            outputs = idef.get("outputs")
            native_lib = idef.get("native_lib", "talib")
            backend_cfg = idef.get("backend", "auto")
            params_list = idef.get("params", [{}])
            if not isinstance(params_list, list):
                params_list = [params_list]
            for params in params_list:
                p = _normalize_params(params)
                col_prefix = _make_col_prefix(category, iname, p)
                spec = dict(category=category, iname=iname, params=p, outputs=outputs,
                            backend_cfg=backend_cfg, native_lib=native_lib,
                            col_prefix=col_prefix)
                if outputs:
                    for o in outputs:
                        specs[f"{col_prefix}_{o}"] = spec
                else:
                    specs[col_prefix] = spec
    return specs


def compute_selected(df: pd.DataFrame, specs: list[dict]) -> pd.DataFrame:
    """只算给定规格里的指标,返回 (index=df.index, 列为新列名) 的 DataFrame。"""
    frames: dict[str, pd.Series] = {}
    for spec in specs:
        backend = _pick_backend(spec["category"], spec["iname"],
                                spec["native_lib"], spec["backend_cfg"])
        fn = talib_calc if backend == "talib" else pandas_ta_calc
        try:
            r = fn(df, spec["category"], spec["iname"], spec["params"],
                   spec["outputs"], spec["col_prefix"])
        except Exception as e:
            raise RuntimeError(
                f"{spec['category']}/{spec['iname']}{spec['params']} 计算失败: "
                f"{type(e).__name__}: {e}") from e
        for col in r.columns:
            frames[col] = r[col]
    return pd.DataFrame(frames, index=df.index)


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

def table_columns(con) -> set[str]:
    rows = con.execute(
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_name = '{TABLE}'"
    ).fetchall()
    return {r[0] for r in rows}


def ensure_columns(con, cols: list[str]) -> int:
    added = 0
    for col in cols:
        try:
            con.execute(f'ALTER TABLE {TABLE} ADD COLUMN "{col}" DOUBLE')
            added += 1
            print(f"  + ALTER ADD COLUMN {col}")
        except duckdb.Error as e:
            msg = str(e).lower()
            if "already exists" in msg or "duplicate column" in msg:
                continue
            raise
    con.commit()
    return added


def scan_null_columns(con, have: set[str], window: int, threshold: float) -> list[str]:
    """找出「已建但基本没数据」的列 —— 夜间增量任务漏算时靠它兜底。

    window 要够长:有些指标结构性尾部为 NaN(例如 ichimoku 的 chikou 是迟行线,
    最后 26 根必然为空)。用 30 天窗口会把 chikou 误判成坏列,所以默认 120。
    """
    latest = con.execute(f"SELECT MAX(date) FROM {TABLE}").fetchone()[0]
    start_d = latest - timedelta(days=window)
    total = con.execute(
        f"SELECT COUNT(*) FROM {TABLE} WHERE date >= '{start_d}'"
    ).fetchone()[0]
    if not total:
        return []
    # 只在 config 声明范围内扫,避免把 metadata 列算进来
    declared = {c for c, _ in expand_columns(_load_config())}
    candidates = sorted((have & declared))
    bad: list[str] = []
    for col in candidates:
        nn = con.execute(
            f'SELECT COUNT("{col}") FROM {TABLE} WHERE date >= \'{start_d}\''
        ).fetchone()[0]
        ratio = nn / total
        if ratio < threshold:
            bad.append(col)
    print(f"  [null-scan] 窗口 {start_d}~{latest} ({total:,} 行), "
          f"阈值 {threshold:.0%}, 命中 {len(bad)} 列")
    return bad


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--codes", type=str, default=None, help="逗号分隔;默认全库")
    p.add_argument("--only", type=str, default=None,
                   help="只处理这些指标名(逗号分隔),其余视为已存在")
    p.add_argument("--targets", type=str, default=None,
                   help="显式指定要回填的指标名(逗号分隔),无视该列是否已建。"
                        "列已存在但数据为空时用这个。")
    p.add_argument("--null-scan", action="store_true",
                   help="自动挑出「已建但基本没数据」的列来回填(夜间增量漏算的兜底)")
    p.add_argument("--scan-window", type=int, default=120,
                   help="--null-scan 的回看天数,默认 120(要 > 结构性尾部 NaN 的长度)")
    p.add_argument("--scan-threshold", type=float, default=0.50,
                   help="--null-scan 的非 NULL 率下限,低于此值判为待回填")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--lookback-days", type=int, default=6000,
                   help="回填起点距今多少天;默认 6000 ≈ 全量 10 年")
    p.add_argument("--batch-chunk", type=int, default=400, help="每批多少票")
    p.add_argument("--dry-run", action="store_true", help="只报告,不 ALTER 不写")
    args = p.parse_args()

    t_total = time.time()
    cfg = _load_config()
    specs = build_specs(cfg)

    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        specs = {c: s for c, s in specs.items() if s["iname"] in wanted}
        print(f"--only 过滤后涉及 {len(specs)} 列 / 指标 {sorted(wanted)}")
        if not specs:
            print("没有匹配的指标,检查 --only 拼写(用 config 里的 name 字段)")
            return 2

    # CDL 由 candles.all_cdl 批量生成,不在本脚本职责内,只用于完整性比对
    cdl_cols = {c for c, _ in expand_cdl_columns()}

    con = duckdb.connect(str(INDICATORS_DB))
    try:
        have = table_columns(con)
        declared = {col for col, _ in expand_columns(cfg)} | cdl_cols
        missing = sorted(declared - have)

        print("=== Step 1: config 声明 vs 表内实际 ===")
        print(f"  config 声明列: {len(declared)}   表内现有列: {len(have)}")
        print(f"  尚未建列: {len(missing)} 列")
        for c in missing:
            print(f"    + {c}")

        # --- 决定回填目标 ---
        # 注意:「列已存在」不等于「列有数据」。表可以已经有这列但整列为 NULL
        # (列是上次 ALTER 建的、数据还没回填),所以目标列的选取有三条路:
        target_cols: list[str]
        if args.targets:
            wanted = {s.strip() for s in args.targets.split(",")}
            specs = {c: s for c, s in specs.items() if s["iname"] in wanted}
            target_cols = sorted(c for c in specs if c in have or c in declared)
            if not target_cols:
                print(f"  --targets {sorted(wanted)} 没匹配到任何列")
                return 2
        elif args.null_scan:
            target_cols = scan_null_columns(con, have, args.scan_window, args.scan_threshold)
        else:
            target_cols = missing

        if not target_cols:
            print("\n没有待回填的列(退出 0)。"
                  "若列已建但数据为空,用 --null-scan 自动识别,"
                  "或用 --targets <指标名> 显式指定。")
            return 0

        print(f"\n  本次回填目标: {len(target_cols)} 列")
        for c in target_cols:
            print(f"    * {c}{'  (已存在)' if c in have else '  (需 ALTER)'}")

        if args.dry_run:
            print("\n--dry-run: 未做任何写入。")
            return 0

        print("\n=== Step 2: ALTER TABLE ===")
        n_added = ensure_columns(con, target_cols)
        print(f"  新增 {n_added} 列(其余已存在)")

        latest = con.execute(f"SELECT MAX(date) FROM {TABLE}").fetchone()[0]
        start_d = latest - timedelta(days=args.lookback_days)
        print(f"\n  回填区间: {start_d} → {latest} ({args.lookback_days} 天)")

        # 只保留真正要算的规格(去重到指标级)
        need_cols = set(target_cols)
        specs_for_compute: list[dict] = []
        seen: set[tuple] = set()
        for col in need_cols:
            spec = specs.get(col)
            if spec is None:
                print(f"  [warn] 列 {col} 在 config 规格里找不到,跳过")
                continue
            key = (spec["category"], spec["iname"], tuple(map(str, spec["params"])),
                   tuple(spec["outputs"]) if spec["outputs"] else None)
            if key in seen:
                continue
            seen.add(key)
            specs_for_compute.append(spec)
        print(f"  涉及 {len(specs_for_compute)} 个指标计算规格")

        print("\n=== Step 3: 选票 ===")
        if args.codes:
            codes = [c.strip() for c in args.codes.split(",")]
        else:
            rows = con.execute(f"SELECT DISTINCT thscode FROM {TABLE}").fetchall()
            codes = [r[0] for r in rows]
        if args.limit:
            codes = codes[:args.limit]
        print(f"  票数: {len(codes)}, batch_chunk: {args.batch_chunk}")

        # upsert 目标列
        upsert_cols = target_cols
        col_list = ", ".join(upsert_cols)
        set_list = ", ".join(f'"{c}" = excluded."{c}"' for c in upsert_cols)

        print(f"\n=== Step 4: 逐批 load_many + 只算 {len(upsert_cols)} 列 + 批量 upsert ===")
        n_done = n_err = 0
        t0 = time.time()
        first_err: list[str] = []

        for start in range(0, len(codes), args.batch_chunk):
            chunk = codes[start:start + args.batch_chunk]
            idx = start // args.batch_chunk + 1
            total_chunks = (len(codes) + args.batch_chunk - 1) // args.batch_chunk
            t_chunk = time.time()

            try:
                data = load_many(chunk, start=str(start_d))
            except Exception as e:
                print(f"  [err] chunk {idx} load: {type(e).__name__}: {e}")
                n_err += len(chunk)
                continue
            if not data:
                print(f"  chunk {idx}: 无数据")
                continue
            load_dt = time.time() - t_chunk

            t_c = time.time()
            parts, bad = [], 0
            for code, df in data.items():
                if df.empty:
                    continue
                try:
                    calc = compute_selected(df, specs_for_compute)
                except Exception as e:
                    bad += 1
                    if len(first_err) < 5:
                        first_err.append(f"{code}: {e}")
                    continue
                calc = calc.reset_index()
                if "date" not in calc.columns:
                    calc = calc.rename(columns={calc.columns[0]: "date"})
                calc.insert(0, "thscode", code)
                calc["backend"] = "talib|pandas_ta|add_indicators"
                calc["computed_at"] = pd.Timestamp.now()
                parts.append(calc)
            if parts:
                blob = pd.concat(parts, ignore_index=True)
                con.register("add_ind_tmp", blob)
                try:
                    con.execute(f"""
                        INSERT INTO {TABLE} (thscode, date, backend, computed_at, {col_list})
                        SELECT thscode, date, backend, computed_at, {col_list}
                        FROM add_ind_tmp
                        ON CONFLICT (thscode, date) DO UPDATE SET
                            backend = excluded.backend,
                            computed_at = excluded.computed_at,
                            {set_list}
                    """)
                finally:
                    con.unregister("add_ind_tmp")
            con.commit()

            n_done += len(parts)
            n_err += bad
            elapsed = time.time() - t0
            rate = n_done / elapsed if elapsed > 0 else 0
            eta = (len(codes) - n_done) / rate if rate > 0 else 0
            print(f"  chunk {idx}/{total_chunks}: load {load_dt:.1f}s, "
                  f"calc+upsert {time.time()-t_c:.1f}s | "
                  f"{n_done}/{len(codes)} ({rate:.1f}/s, ETA {eta/60:.1f}min)")

        print("\n=== Step 5: 验证 ===")
        for c in upsert_cols:
            nn = con.execute(
                f'SELECT COUNT(*) FROM {TABLE} WHERE date >= \'{start_d}\' AND "{c}" IS NOT NULL'
            ).fetchone()[0]
            tt = con.execute(
                f"SELECT COUNT(*) FROM {TABLE} WHERE date >= '{start_d}'"
            ).fetchone()[0]
            print(f"  {c:<34} 非 NULL {nn:>10,} / {tt:>10,}  ({nn/tt*100:5.1f}%)")
    finally:
        con.close()

    if first_err:
        print("\n计算失败样例:")
        for e in first_err:
            print(f"  {e}")

    print(f"\n=== Done: {n_done} ok, {n_err} err, {time.time()-t_total:.1f}s ===")
    return 10 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
