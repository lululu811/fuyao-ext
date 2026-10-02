"""fix_kc_columns.py — 重算 Keltner 三列(2026-10-01)

为什么单独一个脚本:
  indicators_config.yaml 的 kc.outputs 写成 [upper, middle, lower],而
  pandas_ta_classic.kc() 返回顺序是 [lower, middle, upper]。adapter 的
  calc_kc 按位置建字典后又用 outputs 重排,于是 upper 列拿到了 lower 的值。
  实测全库 100% 的行 kc_upper < kc_lower,直接导致 Keltner 挤压信号永不触发
  (见 hithink_finance/pattern/signal_frequency_audit.md 记为 dead)。

为什么不走 add_indicators.py 重算全表:
  那条路径 import talib,而当前机器任何 Python 环境都没装 talib(Keltner 列
  之所以一直是错的,根因就在这里 —— 全量重建从未成功跑过)。本脚本只需要
  pandas + pandas_ta_classic + 行情库,依赖面小得多。

已同时修好两处,本脚本只负责把数据补上:
  - indicators_config.yaml: outputs 改成 [lower, middle, upper]
  - indicator/adapter_pandas_ta.py:calc_kc 改为按角色名落位,与 outputs 顺序无关

退出码: 0 通过 / 11 校验不过
"""
from __future__ import annotations

import argparse
import sys
import time

import duckdb
import pandas as pd
import pandas_ta_classic as ta

from indicator.loader import load_many
from paths import INDICATORS_DB

COLS = {
    "volatility_kc_20_2_lower": "lower",
    "volatility_kc_20_2_middle": "middle",
    "volatility_kc_20_2_upper": "upper",
}
ROLE_BY_PREFIX = {"KCLe": "lower", "KCBe": "middle", "KCUe": "upper"}


def calc_kc_cols(df: pd.DataFrame) -> pd.DataFrame:
    """返回**库列名**的 lower/middle/upper 三列 —— 与 adapter 的修法一致。

    ta.kc() 的角色名(lower/middle/upper)在这里直接映射成 DuckDB 列名,
    不依赖 indicators_config.yaml 的 outputs 顺序。
    """
    r = ta.kc(df["high"], df["low"], df["close"], length=20, scalar=2)
    by_role = {ROLE_BY_PREFIX[c.split("_")[0]]: r[c] for c in r.columns}
    missing = [k for k in ROLE_BY_PREFIX.values() if k not in by_role]
    if missing:
        raise ValueError(f"kc: 缺少 {missing}")
    return pd.DataFrame({col: by_role[role] for col, role in COLS.items()})


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--codes", type=str, default=None,
                   help="逗号分隔的 thscode 列表，只重算这些票")
    p.add_argument("--batch-chunk", type=int, default=500)
    p.add_argument("--verify-only", action="store_true")
    args = p.parse_args()

    t0 = time.time()
    con = duckdb.connect(str(INDICATORS_DB))
    if args.verify_only:
        ok = verify(con)
        con.close()
        sys.exit(0 if ok else 11)
    try:
        if args.codes:
            codes = [c.strip() for c in args.codes.split(",") if c.strip()]
        else:
            codes = [r[0] for r in con.execute(
                "SELECT DISTINCT thscode FROM v_indicators_daily ORDER BY thscode"
            ).fetchall()]
    finally:
        con.close()
    if args.limit:
        codes = codes[:args.limit]
    rconn = duckdb.connect(str(INDICATORS_DB), read_only=True)
    try:
        lo = rconn.execute("SELECT min(date) FROM v_indicators_daily").fetchone()[0]
    finally:
        rconn.close()
    print(f"票数 {len(codes)} | 重算区间 {lo} → 至今")

    con = duckdb.connect(str(INDICATORS_DB))
    n_done = n_err = 0
    for i in range(0, len(codes), args.batch_chunk):
        chunk = codes[i:i + args.batch_chunk]
        try:
            data = load_many(chunk)
        except Exception as e:
            print(f"  [err] load {i}: {e}")
            n_err += len(chunk)
            continue
        for code, df in data.items():
            # KC 需要 20 根预热（pandas-ta 的 kc 在 index < 20 时给 NaN）。
            # 此前用 25 作门槛，把 21~24 根的次新股整只跳过了，于是它们残留
            # 上一轮颠倒的旧值 —— 2026-10-01 首次全量重算后仍有 5 行颠倒，
            # 全部来自 3 只 21~23 根 bar 的次新股。
            if df is None or len(df) < 20:
                continue
            try:
                kc = calc_kc_cols(df).reset_index()
                kc.insert(0, "thscode", code)
                con.register("kc_batch", kc)
                # 用 INSERT ... ON CONFLICT 而不是 UPDATE ... FROM：
                # 后者不支持 excluded 别名(DuckDB 只在 upsert 语法里给这个别名)。
                # backend / computed_at 是 NOT NULL,upsert 新行时必须带上 ——
                # 沿用 v_indicators_daily 既有的 backend 标记,表明这一列由
                # pandas_ta 产出,不要伪装成 talib。
                sets = ", ".join(f"{c} = excluded.{c}" for c in COLS)
                con.execute(f"""
                    INSERT INTO v_indicators_daily
                        (thscode, date, backend, computed_at, {", ".join(COLS)})
                    SELECT thscode, date, 'pandas_ta', now(), {", ".join(COLS)}
                    FROM kc_batch
                    ON CONFLICT (thscode, date) DO UPDATE SET {sets}
                """)
                con.unregister("kc_batch")
                n_done += 1
            except Exception as e:
                n_err += 1
                if n_err <= 3:
                    print(f"  [err] {code}: {type(e).__name__}: {e}")
        con.commit()
        print(f"  {i + len(chunk)}/{len(codes)} ({n_done} ok, {n_err} err, "
              f"{time.time() - t0:.0f}s)")
    con.close()

    con = duckdb.connect(str(INDICATORS_DB))
    ok = verify(con)
    con.close()
    print(f"=== Done: {n_done} ok, {n_err} err, {time.time() - t0:.1f}s ===")
    if n_err:
        print(f"⛔ {n_err} 只票回填失败 —— 退出码非零，别当成功。")
        sys.exit(12)
    sys.exit(0 if ok else 11)


def verify(con) -> bool:
    """Keltner 的定义性质:lower < middle < upper 必须逐行成立。"""
    print("\n=== 校验 ===")
    bad = con.execute("""
        SELECT count(*) FROM v_indicators_daily
        WHERE volatility_kc_20_2_lower > 0
          AND NOT (volatility_kc_20_2_lower < volatility_kc_20_2_middle
                   AND volatility_kc_20_2_middle < volatility_kc_20_2_upper)
    """).fetchone()[0]
    tot = con.execute("""
        SELECT count(*) FROM v_indicators_daily WHERE volatility_kc_20_2_lower > 0
    """).fetchone()[0]
    print(f"  上下轨颠倒的行: {bad:,} / {tot:,}")
    sample = con.execute("""
        SELECT date, volatility_kc_20_2_lower, volatility_kc_20_2_middle,
               volatility_kc_20_2_upper
        FROM v_indicators_daily
        WHERE thscode = '601398.SH' ORDER BY date DESC LIMIT 3
    """).fetchall()
    for s in sample:
        print(f"  {s[0]}  lower={s[1]:.3f} mid={s[2]:.3f} upper={s[3]:.3f}")
    if bad:
        print(f"  ⛔ 仍有 {bad:,} 行上下轨颠倒")
        return False
    print("  ✅ 全部行满足 lower < middle < upper")
    return True


if __name__ == "__main__":
    main()
