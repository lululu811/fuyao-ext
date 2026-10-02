"""add_zettaranc_columns.py — v4, 只算 6 列(不重算 225 列)

v1 (load_one + per-ticket connect): 0.4/s
v2 (单连接批 INSERT,load_one):    0.5/s
v3 (load_many + compute_one):     0.5/s  ← compute_one 是瓶颈(229 列)
v4 (load_many + compute only 6): 期望 10-20/s

为什么快:
  - compute_one 跑 229 列(sma_5/10/20/60/120/250 + 61 CDL 等),占 99% 时间
  - 只算 6 列 ≈ 50x 加速

退出码: 0 干净 / 10 降级

历史备注:
  本脚本此前靠 `sys.path.insert(ROOT / "pandas-ta-classic")` 注入一个仓库内的
  本地依赖目录（目录名带连字符，Python 无法自动发现）。而这行 import 恰好
  排在 sys.path.insert 之前，于是每次运行都在此处 ModuleNotFoundError 崩溃，
  6 列从未被真正计算过。
  依赖现已改为 pyproject 正常声明，隐式路径注入已移除。线上表实测 6 列
  非空率 96.9%~100%、零值行数为 0，数据正常可用 —— 该历史问题已解决。
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import timedelta

import duckdb
import pandas as pd
import pandas_ta_classic as ta

from indicator.loader import load_many
from paths import INDICATORS_DB

# 每列产出第一个值所需的最少 bar 数(= 最长依赖的窗口长度)。
# 窗口开头这些 bar 上是 NULL 属于**正确行为**,验证时不能算作缺陷 ——
# 闸门据此只在预热期之后统计非空率。
WARMUP_BARS = {
    "zettaranc_zg_white_10": 19,      # DEMA(EMA(C,10),10) → 约 2*10-1
    "zettaranc_dg_yellow_14": 114,    # (MA14+MA28+MA57+MA114)/4
    "zettaranc_bbi": 24,              # (MA3+MA6+MA12+MA24)/4
    "zettaranc_brick_value": 4,       # HHV/LLV(4) + 两级 SMA
    "zettaranc_rsl_rank_15": 3 + 15,  # pct_change(3) 后 15 窗口排名
    "zettaranc_rsl_rank_105": 21 + 105,  # pct_change(21) 后 105 窗口排名
}

NEW_COLUMNS = [
    "zettaranc_zg_white_10",
    "zettaranc_dg_yellow_14",
    "zettaranc_bbi",
    "zettaranc_brick_value",
    # RSL 是**滚动窗口百分位排名**,不是涨跌幅。窗口长度写进列名,
    # 免得再被当成 % 涨跌幅读(此前 *_short_3 / *_long_21 里的 3/21 是
    # pct_change 的回看天数,不是窗口 —— 名字本身就是误导的来源)。
    "zettaranc_rsl_rank_15",
    "zettaranc_rsl_rank_105",
]


def compute_zettaranc_only(df: pd.DataFrame) -> pd.DataFrame:
    """只算 6 个 zettaranc 列,返回 DataFrame(同 index)."""
    close = df["close"]
    high = df["high"]
    low = df["low"]

    # 1. 白线: EMA(EMA(C, 10), 10)
    zg_white = ta.ema(ta.ema(close, length=10), length=10)

    # 2. 黄线: (MA14+MA28+MA57+MA114)/4
    dg_yellow = (
        ta.sma(close, length=14)
        + ta.sma(close, length=28)
        + ta.sma(close, length=57)
        + ta.sma(close, length=114)
    ) / 4.0

    # 3. BBI: (MA3+MA6+MA12+MA24)/4
    bbi = (
        ta.sma(close, length=3)
        + ta.sma(close, length=6)
        + ta.sma(close, length=12)
        + ta.sma(close, length=24)
    ) / 4.0

    # 4. 砖型图(知行 ZX 砖型,通达信口径)
    #
    # 此前这里是 (close-open)/(high-low) —— 一个归一化实体比例,值域 [-1,1]。
    # 而工作台画的是另一套东西(见 WeKnora frontend/.../stock-score.ts:166
    # calcZXBrick),前端才是你看盘时真正对照的那个。两者**不是同一个指标**,
    # 此前同名列并存,所以本列的 0 值无法解释前端行为。
    #
    # 权威定义(短周期砖型图 v2026.docx / indicators.yaml ZX_BRICK):
    #   VAR1A = (HHV(HIGH,4) - C) / (HHV(HIGH,4) - LLV(LOW,4)) * 100 - 90
    #   VAR2A = SMA(VAR1A, 4, 1) + 100
    #   VAR3A = (C - LLV(LOW,4)) / (HHV(HIGH,4) - LLV(LOW,4)) * 100
    #   VAR4A = SMA(VAR3A, 6, 1)
    #   VAR5A = SMA(VAR4A, 6, 1) + 100
    #   VAR6A = VAR5A - VAR2A
    #   砖型  = IF(VAR6A > 4, VAR6A - 4, 0)
    #
    # 值域是 [0, +),不是 [-100,100] —— 实测库里 [-100,100] 那个值域正是
    # 旧 RSL 口径留下的,现在 RSL 已改名,这里也不再产生负值。
    brick = _calc_zx_brick(high, low, close)

    # 5/6. RSL: 短/长 N 日涨幅在滚动窗口内的**百分位排名**
    #
    # 这是 RSL 的原义(Relative Strength *Line* = 相对强弱位),不是涨跌幅。
    # 工作台前端画的那条是 %涨跌幅(indicators.ts:184),同名不同义 —— 见
    # WeKnora config/indicators.yaml Z_RSL。列名改为 *_rank_15 / *_rank_105
    # 把"窗口长度"也写进名字,避免再被当成涨跌幅读。
    pct_3 = close.pct_change(periods=3) * 100
    pct_21 = close.pct_change(periods=21) * 100
    rsl_short = pct_3.rolling(15, min_periods=3).rank(pct=True) * 100
    rsl_long = pct_21.rolling(105, min_periods=21).rank(pct=True) * 100

    return pd.DataFrame({
        "zettaranc_zg_white_10": zg_white,
        "zettaranc_dg_yellow_14": dg_yellow,
        "zettaranc_bbi": bbi,
        "zettaranc_brick_value": brick,
        "zettaranc_rsl_rank_15": rsl_short,
        "zettaranc_rsl_rank_105": rsl_long,
    }, index=df.index)


def _tonghuashun_sma(values, n: int, m: int):
    """通达信/同花顺 SMA(X, N, M): Y = (M*X + (N-M)*Y') / N,首值 Y = X。

    与 stock-score.ts:96 calcTongHuaShunSMA 逐字对应。
    """
    out = []
    prev = None
    for x in values:
        if prev is None:
            prev = x
        else:
            prev = (m * x + (n - m) * prev) / n
        out.append(prev)
    return pd.Series(out, index=values.index, dtype="float64")


def _calc_zx_brick(high, low, close) -> pd.Series:
    """知行 ZX 砖型图,通达信口径。与前端 calcZXBrick 逐字对应。"""
    n = len(close)
    var1a = [float("nan")] * n
    var3a = [float("nan")] * n
    for i in range(n):
        start = max(0, i - 3)
        window_high = high.iloc[start:i + 1]
        window_low = low.iloc[start:i + 1]
        hhv = window_high.max()
        llv = window_low.min()
        c = close.iloc[i]
        rng = max(hhv - llv, 0.0001)
        var1a[i] = (hhv - c) / rng * 100.0 - 90.0
        var3a[i] = (c - llv) / rng * 100.0

    idx = close.index
    s1 = pd.Series(var1a, index=idx, dtype="float64")
    s3 = pd.Series(var3a, index=idx, dtype="float64")
    var2a = _tonghuashun_sma(s1, 4, 1) + 100.0
    var4a = _tonghuashun_sma(s3, 6, 1)
    var5a = _tonghuashun_sma(var4a, 6, 1) + 100.0
    var6a = var5a - var2a
    return pd.Series(
        [round(v - 4.0, 2) if v > 4.0 else 0.0 for v in var6a],
        index=idx, dtype="float64",
    )


def ensure_columns(con) -> int:
    added = 0
    for col in NEW_COLUMNS:
        try:
            con.execute(f"ALTER TABLE v_indicators_daily ADD COLUMN {col} DOUBLE")
            added += 1
            print(f"  + ALTER ADD COLUMN {col}")
        except duckdb.Error as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                continue
            raise
    con.commit()
    return added


def upsert_one(con, code: str, df: pd.DataFrame) -> bool:
    """算 + upsert 一只票的6 列."""
    new_cols = compute_zettaranc_only(df).reset_index()
    new_cols.insert(0, "thscode", code)
    new_cols["backend"] = "zettaranc_migrate"
    new_cols["computed_at"] = pd.Timestamp.now()

    con.register("zettaranc_tmp", new_cols)
    try:
        con.execute("""
            INSERT INTO v_indicators_daily
                (thscode, date, backend, computed_at,
                 zettaranc_zg_white_10, zettaranc_dg_yellow_14,
                 zettaranc_bbi, zettaranc_brick_value,
                 zettaranc_rsl_rank_15, zettaranc_rsl_rank_105)
            SELECT thscode, date, backend, computed_at,
                   zettaranc_zg_white_10, zettaranc_dg_yellow_14,
                   zettaranc_bbi, zettaranc_brick_value,
                   zettaranc_rsl_rank_15, zettaranc_rsl_rank_105
            FROM zettaranc_tmp
            ON CONFLICT (thscode, date) DO UPDATE SET
                backend = excluded.backend,
                computed_at = excluded.computed_at,
                zettaranc_zg_white_10 = excluded.zettaranc_zg_white_10,
                zettaranc_dg_yellow_14 = excluded.zettaranc_dg_yellow_14,
                zettaranc_bbi = excluded.zettaranc_bbi,
                zettaranc_brick_value = excluded.zettaranc_brick_value,
                zettaranc_rsl_rank_15 = excluded.zettaranc_rsl_rank_15,
                zettaranc_rsl_rank_105 = excluded.zettaranc_rsl_rank_105
        """)
    finally:
        con.unregister("zettaranc_tmp")
    return True


def main():
    p = argparse.ArgumentParser()
    # 默认值曾是 130 自然日 ≈ 89 根 bar —— 少于黄线所需的 MA114,于是
    # 默认跑一次只能填到窗口末尾一小段,历史永远是 NULL,且没有任何提示。
    # 现在默认覆盖全历史:宁可多算,不要留半截。
    p.add_argument("--lookback-days", type=int, default=3700,
                   help="回溯自然日。必须 >= 最长窗口(MA114≈165日)所需的预热,"
                        "否则窗口开头的列恒为 NULL。默认 3700 覆盖全历史。")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--codes", type=str, default=None)
    p.add_argument("--batch-chunk", type=int, default=500,
                   help="load_many 每批多少票(防内存)")
    p.add_argument("--verify-only", action="store_true",
                   help="只跑校验闸门,不重算。用于改判据后复验已有数据。")
    args = p.parse_args()

    t_total = time.time()

    print("=== Step 1: ALTER TABLE 加新列 ===")
    con = duckdb.connect(str(INDICATORS_DB))
    try:
        n_added = ensure_columns(con)
        if n_added == 0:
            print("  6 列已存在,跳过 ALTER")
        latest = con.execute("SELECT MAX(date) FROM v_indicators_daily").fetchone()[0]
    finally:
        con.close()

    start_d = latest - timedelta(days=args.lookback_days)
    print(f"\n  重算区间: {start_d} → {latest} ({args.lookback_days} 天)")

    print("\n=== Step 2: 选票 ===")
    con = duckdb.connect(str(INDICATORS_DB))
    try:
        if args.codes:
            codes = [c.strip() for c in args.codes.split(",")]
        else:
            rows = con.execute(
                "SELECT DISTINCT thscode FROM v_indicators_daily"
            ).fetchall()
            codes = [r[0] for r in rows]
    finally:
        con.close()
    if args.limit:
        codes = codes[:args.limit]
    print(f"  票数: {len(codes)}")

    if args.verify_only:
        print("\n=== Step 3: 跳过（--verify-only）===")
        print("=== Step 4: 验证（闸门，不通过则非零退出）===")
        ok = verify_zettaranc(start_d, codes)
        print(f"\n=== Done: verify-only, {time.time()-t_total:.1f}s ===")
        if not ok:
            print("\n⛔ 验证未通过 —— 不要让消费侧读它。")
            sys.exit(11)
        return

    print("\n=== Step 3: load_many + 算 6 列 ===")
    print(f"  batch_chunk: {args.batch_chunk}")

    con = duckdb.connect(str(INDICATORS_DB))
    n_done, n_err = 0, 0
    t0 = time.time()

    for chunk_start in range(0, len(codes), args.batch_chunk):
        chunk_codes = codes[chunk_start: chunk_start + args.batch_chunk]
        chunk_idx = chunk_start // args.batch_chunk + 1
        total_chunks = (len(codes) + args.batch_chunk - 1) // args.batch_chunk

        t_chunk = time.time()
        try:
            data = load_many(chunk_codes, start=str(start_d))
        except Exception as e:
            print(f"  [err] chunk {chunk_idx} load: {e}")
            n_err += len(chunk_codes)
            continue
        if not data:
            print(f"  chunk {chunk_idx}: no data")
            continue
        load_dt = time.time() - t_chunk

        t_compute = time.time()
        for code, df in data.items():
            try:
                upsert_one(con, code, df)
                n_done += 1
            except Exception as e:
                n_err += 1
                if n_err <= 5:
                    print(f"  [err] {code}: {type(e).__name__}: {e}")

        con.commit()
        compute_dt = time.time() - t_compute
        elapsed = time.time() - t0
        rate = n_done / elapsed if elapsed > 0 else 0
        eta = (len(codes) - n_done) / rate if rate > 0 else 0
        print(f"  chunk {chunk_idx}/{total_chunks}: load {load_dt:.1f}s, "
              f"compute+upsert {compute_dt:.1f}s | "
              f"{n_done}/{len(codes)} ({rate:.1f}/s, eta {eta/60:.1f}min)")

    con.close()

    print("\n=== Step 4: 验证（闸门，不通过则非零退出）===")
    ok = verify_zettaranc(start_d, codes)

    print(f"\n=== Done: {n_done} ok, {n_err} err, "
          f"{time.time()-t_total:.1f}s ===")
    if not ok:
        print("\n⛔ 验证未通过 —— 数据已写入但不可信,不要让消费侧读它。")
        sys.exit(11)


def verify_zettaranc(start_d, codes) -> bool:
    """回填后的强制校验。

    为什么必须自动:INDICATORS_DB.md 要求"进表前手工复算定义",而 2026-10-01
    这次事故正是跳过了这一步 —— 6 列 99.6% 常数 0 在库里躺了很久没人发现。
    手工流程已经证明会漏,所以闸门绑在脚本上:不通过就非零退出。

    判据(全部基于本脚本刚写的窗口,不跨历史):
      1. 非空率 > 95%          —— 回填失败的特征是几乎全 NULL
      2. 零值率 < 1%           —— 回填失败的特征是几乎全 0(本次事故即如此)
      3. 白线值域为价格量纲     —— 本次事故的实测值域是 [-100,100],白线应贴近 close
      4. 砖型非负              —— 通达信口径 IF(VAR6A>4, VAR6A-4, 0) 恒 >= 0
      5. RSL 落在 [0,100]      —— 百分位排名
      6. 抽样票白线贴近收盘价   —— 抓"算错公式但看着有值"的情况
    """
    con = duckdb.connect(str(INDICATORS_DB), read_only=True)
    failures = []
    try:
        clause = ",".join(f"'{c}'" for c in codes)
        base = (f"FROM v_indicators_daily "
                f"WHERE date >= '{start_d}' AND thscode IN ({clause})")
        total = con.execute(f"SELECT COUNT(*) {base}").fetchone()[0]
        if total == 0:
            print("  ✗ 窗口内无任何行,无法验证")
            return False

        # 预热期:每列在开头若干根 bar 上**必然**是 NULL,这是指标定义要求的,
        # 不是缺陷 —— 黄线要 MA114(≈165 自然日),RSL105 要 105 窗口。
        #
        # 所以非空率只在**「已上市足够久」的票**上算:次新股(2025-06 之后上市)
        # 天然凑不满 114 根 bar,把它们算进分母会让判据永远误报 —— 2026-10-01
        # 全量回填时黄线因此报 98.63%,查证后确认 160 只 NULL 票**全部**是次新,
        # 老票非空率 99.95%。次新股数量随市场变化,不是数据质量信号。
        # 零值率仍在全窗口统计:NULL 是"算不出",0 是"算错了",必须分开判。
        mature = [r[0] for r in con.execute(f"""
            SELECT thscode FROM (
                SELECT thscode, count(*) n FROM v_indicators_daily
                WHERE thscode IN ({clause}) GROUP BY 1
            ) t WHERE n >= 300
        """).fetchall()]
        if not mature:
            print("  ✗ 没有上市满 300 根 bar 的票,无法验证")
            return False
        mclause = ",".join(f"'{c}'" for c in mature)
        n_young = len(codes) - len(mature)
        print(f"  （成熟票 {len(mature)} 只参与非空率判定；"
              f"{n_young} 只需要 {max(WARMUP_BARS.values())} 根 bar 的次新股被排除）")
        mbase = (f"FROM v_indicators_daily WHERE thscode IN ({mclause}) "
                 f"AND date >= (SELECT max(date) - INTERVAL 180 DAY FROM v_indicators_daily)")
        for col in NEW_COLUMNS:
            need = WARMUP_BARS[col]
            zero = con.execute(f"SELECT COUNT(*) {base} AND {col} = 0").fetchone()[0]
            zero_pct = zero / total * 100
            r_tot, r_nn = con.execute(
                f"SELECT count(*), count(*) FILTER (WHERE {col} IS NOT NULL) {mbase}"
            ).fetchone()
            nn_pct = (r_nn / r_tot * 100) if r_tot else 0.0
            print(f"  {col:32s} 预热{need:>4d}根 | 成熟票近期非空 {nn_pct:6.2f}%  "
                  f"全窗零值 {zero_pct:6.2f}%")
            if r_tot and nn_pct <= 99.0:
                failures.append(
                    f"{col} 预热后非空率 {nn_pct:.2f}% <= 99%（需 {need} 根预热）")
            if zero_pct >= 1.0:
                failures.append(f"{col} 全窗零值率 {zero_pct:.2f}% >= 1%")

        # 值域:白线是价格量纲,砖型非负,RSL 是百分位
        wmin, wmax = con.execute(
            f"SELECT min(zettaranc_zg_white_10), max(zettaranc_zg_white_10) {base}"
        ).fetchone()
        print(f"  白线值域 [{wmin}, {wmax}]（应贴近 close 的价格量纲）")
        if wmin is not None and wmin < 0:
            failures.append(f"白线出现负值 {wmin} —— 量纲可疑（本次事故为 [-100,100]）")

        bmin = con.execute(
            f"SELECT min(zettaranc_brick_value) {base} AND zettaranc_brick_value IS NOT NULL"
        ).fetchone()[0]
        print(f"  砖型最小值 {bmin}（通达信口径应 >= 0）")
        if bmin is not None and bmin < 0:
            failures.append(f"砖型出现负值 {bmin} —— 不是通达信口径")

        for col in ("zettaranc_rsl_rank_15", "zettaranc_rsl_rank_105"):
            rmin, rmax = con.execute(
                f"SELECT min({col}), max({col}) {base} AND {col} IS NOT NULL"
            ).fetchone()
            print(f"  {col} 值域 [{rmin}, {rmax}]（百分位应落在 [0,100]）")
            if rmin is not None and (rmin < 0 or rmax > 100):
                failures.append(f"{col} 值域 [{rmin},{rmax}] 越出 [0,100]")

        # 抽样:白线与收盘价的偏离。
        # 收盘价**不在 indicators.duckdb 里**(该库只有 v_indicators_daily
        # 一张表),它在 market.duckdb —— 两个库是独立只读连接,不能 join,
        # 所以把白线样本拉出来用 pandas 对齐。
        #
        # 必须抽样:全量是 1024 万行 × 5572 只票,逐行 reindex 要跑 20 分钟,
        # 闸门本身就成了最慢的一步。抽样用**固定跨步**(而不是随机),跨遍
        # 全部代码前缀且可复现 —— 同一份数据两次跑得到同一批样本。
        SAMPLE_TICKERS = 60
        step = max(1, len(mature) // SAMPLE_TICKERS)
        sampled = mature[::step][:SAMPLE_TICKERS]
        sclause = ",".join(f"'{c}'" for c in sampled)
        sbase = (f"FROM v_indicators_daily WHERE thscode IN ({sclause}) "
                 f"AND zettaranc_zg_white_10 IS NOT NULL "
                 f"AND date >= DATE '{start_d}'")
        samples = con.execute(
            f"SELECT thscode, date, zettaranc_zg_white_10 {sbase}").fetchall()
        px = load_many(sorted(sampled), start=str(start_d))
        dev = 0
        checked = 0
        for code, d, white in samples:
            df = px.get(code)
            if df is None:
                continue
            ref = df["close"].reindex([d])
            if ref.empty or not ref.iloc[0] or ref.iloc[0] <= 0:
                continue
            checked += 1
            if abs(white - float(ref.iloc[0])) / float(ref.iloc[0]) > 0.5:
                dev += 1
        print(f"  白线对齐收盘价: 抽样 {len(sampled)} 只 / 检查 {checked} 行, "
              f"偏离 >50% 的 {dev} 行")
        if checked == 0:
            failures.append("无法对齐任何收盘价 —— 判据 6 失效,不能算通过")
        elif dev > checked * 0.01:
            failures.append(f"{dev}/{checked} 行白线偏离收盘价 >50%")
    finally:
        con.close()

    if failures:
        print("\n  ⛔ 未通过:")
        for f in failures:
            print(f"     - {f}")
        return False
    print("\n  ✅ 全部判据通过")
    return True


if __name__ == "__main__":
    main()
