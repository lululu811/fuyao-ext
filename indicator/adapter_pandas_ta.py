"""adapter_pandas_ta.py — pandas-ta-classic 适配器 (不兜底)

每个函数直接调 pandas-ta,严格按真实返回值处理.
- Series -> 单列 DataFrame,列名 = col_prefix
- DataFrame -> 多列,按 outputs 1:1 映射
- outputs 数量跟实际列数不符 -> 抛 ValueError(compute.py 捕获并 warn)
"""

from __future__ import annotations

import pandas as pd
import pandas_ta_classic as ta


def _to_series(result) -> pd.Series:
    if result is None:
        raise ValueError("pandas-ta returned None")
    if isinstance(result, pd.DataFrame):
        if result.shape[1] == 1:
            return result.iloc[:, 0]
        raise ValueError(f"expected Series, got DataFrame with {result.shape[1]} cols: {list(result.columns)}")
    if isinstance(result, pd.Series):
        return result
    raise ValueError(f"unexpected type: {type(result)}")


def _to_dataframe(result) -> pd.DataFrame:
    if result is None:
        raise ValueError("pandas-ta returned None")
    if not isinstance(result, pd.DataFrame):
        raise ValueError(f"expected DataFrame, got {type(result)}")
    return result


def _series_to_df(s: pd.Series, col_name: str) -> pd.DataFrame:
    return s.to_frame(col_name)


def _df_rename_cols(df: pd.DataFrame, new_cols: list[str]) -> pd.DataFrame:
    if len(new_cols) != df.shape[1]:
        raise ValueError(f"need {df.shape[1]} new names, got {len(new_cols)}")
    out = df.copy()
    out.columns = new_cols
    return out


# === overlap ===

def calc_kdj(df, params, col_prefix, outputs):
    length, signal = params[0], params[1]
    result = ta.kdj(df["high"], df["low"], df["close"], length=length, signal=signal)
    df_out = _to_dataframe(result)
    rename = {c: c.split("_")[0].lower() for c in df_out.columns}
    df_out = df_out.rename(columns=rename)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"kdj: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_kc(df, params, col_prefix, outputs):
    length, std = params[0], params[1]
    result = ta.kc(df["high"], df["low"], df["close"], length=length, scalar=std)
    df_out = _to_dataframe(result)
    # 按**角色名**落位,不按位置。此前先按位置建 ordered 字典、再用
    # outputs 列表重排,于是 outputs 的顺序必须与 pandas-ta 返回顺序完全
    # 一致,否则 upper/lower 互换 —— indicators_config.yaml 曾写
    # [upper, middle, lower] 而 pandas-ta 返回 [lower, middle, upper],
    # 结果全库 100% 的 kc_upper < kc_lower,Keltner 挤压信号永不触发。
    # 配置顺序不该有这种威力:roles 按名字取,顺序由代码固定。
    ROLE_BY_PREFIX = {"KCLe": "lower", "KCBe": "middle", "KCUe": "upper"}
    by_role = {}
    for col in df_out.columns:
        role = ROLE_BY_PREFIX.get(col.split("_")[0])
        if role is None:
            raise ValueError(f"kc: 无法识别的列名 {col}")
        by_role[role] = df_out[col]
    missing = [r for r in ("lower", "middle", "upper") if r not in by_role]
    if missing:
        raise ValueError(f"kc: 缺少 {missing}")
    if len(outputs) != 3:
        raise ValueError(f"kc: expected 3 outputs, got {outputs}")
    # 列名按 outputs 声明的顺序生成（upper/middle/lower 都能得到正确值），
    # 顺序只影响列的位置，不影响值。
    df_out = pd.DataFrame({r: by_role[r] for r in outputs})
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_cmf(df, params, col_prefix, outputs):
    s = _to_series(ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=params[0]))
    return _series_to_df(s, col_prefix)


def calc_vwap(df, params, col_prefix, outputs):
    s = _to_series(ta.vwap(df["high"], df["low"], df["close"], df["volume"]))
    return _series_to_df(s, col_prefix)


def _single_overlap(name):
    fn = getattr(ta.overlap, name)
    def calc(df, params, col_prefix, outputs):
        return _series_to_df(_to_series(fn(df["close"], length=params[0])), col_prefix)
    return calc


def calc_hma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.hma(df["close"], length=params[0])), col_prefix)


def calc_alma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.alma(df["close"], length=params[0])), col_prefix)


def calc_vidya(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.vidya(df["close"], length=params[0])), col_prefix)


def calc_rma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.rma(df["close"], length=params[0])), col_prefix)


def calc_zlma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.zlma(df["close"], length=params[0])), col_prefix)


def calc_mcgd(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.mcgd(df["close"], length=params[0])), col_prefix)


def calc_fwma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.fwma(df["close"], length=params[0])), col_prefix)


def calc_hwma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.hwma(df["close"])), col_prefix)


def calc_jma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.jma(df["close"], length=params[0])), col_prefix)


def calc_pwma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.pwma(df["close"], length=params[0])), col_prefix)


def calc_swma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.swma(df["close"], length=params[0])), col_prefix)


def calc_ssf(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.ssf(df["close"], length=params[0])), col_prefix)


def calc_sinwma(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.sinwma(df["close"], length=params[0])), col_prefix)


# === momentum ===

def calc_stochf(df, params, col_prefix, outputs):
    fastk, fastd = params[0], params[1]
    result = ta.stochf(df["high"], df["low"], df["close"], fastk=fastk, fastd=fastd)
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"stochf: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_er(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.er(df["close"], length=params[0])), col_prefix)


def calc_eri(df, params, col_prefix, outputs):
    result = ta.eri(df["high"], df["low"], df["close"], length=params[0])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"eri: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_fisher(df, params, col_prefix, outputs):
    length, signal = params[0], params[1]
    result = ta.fisher(df["high"], df["low"], length=length, signal=signal)
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"fisher: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_qqe(df, params, col_prefix, outputs):
    length, smooth = params[0], params[1]
    result = ta.qqe(df["close"], length=length, smooth=smooth)
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"qqe: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_rsx(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.rsx(df["close"], length=params[0])), col_prefix)


def calc_smi(df, params, col_prefix, outputs):
    fast, slow, signal = params[0], params[1], params[2]
    result = ta.smi(df["close"], fast=fast, slow=slow, signal=signal)
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"smi: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_dm(df, params, col_prefix, outputs):
    result = ta.dm(df["high"], df["low"], length=params[0])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"dm: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


# === trend ===

def calc_dpo(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.dpo(df["close"], length=params[0])), col_prefix)


def calc_vortex(df, params, col_prefix, outputs):
    result = ta.vortex(df["high"], df["low"], df["close"], length=params[0])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"vortex: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_supertrend(df, params, col_prefix, outputs):
    length, multiplier = params[0], params[1]
    result = ta.overlap.supertrend(df["high"], df["low"], df["close"], length=length, multiplier=multiplier)
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"supertrend: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_chop(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.chop(df["high"], df["low"], df["close"], length=params[0])), col_prefix)


def calc_inertia(df, params, col_prefix, outputs):
    s = ta.inertia(df["close"], high=df["high"], low=df["low"], length=params[0])
    return _series_to_df(_to_series(s), col_prefix)


def calc_decay(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.decay(df["close"], length=params[0])), col_prefix)


# === volume ===

def calc_emv(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.emv(df["high"], df["low"], df["volume"])), col_prefix)


def calc_eom(df, params, col_prefix, outputs):
    raw = ta.eom(df["high"], df["low"], df["close"], df["volume"], length=params[0])
    return _series_to_df(_to_series(raw), col_prefix)


def calc_kvo(df, params, col_prefix, outputs):
    fast, slow = params[0], params[1]
    result = ta.kvo(df["high"], df["low"], df["close"], df["volume"], fast=fast, slow=slow)
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"kvo: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_aobv(df, params, col_prefix, outputs):
    fast, slow = params[0], params[1]
    result = ta.aobv(df["close"], df["volume"], fast=fast, slow=slow)
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"aobv: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_vfi(df, params, col_prefix, outputs):
    length, coef = params[0], params[1]
    return _series_to_df(_to_series(ta.vfi(df["close"], df["volume"], length=length, coef=coef)), col_prefix)


def calc_wad(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.wad(df["high"], df["low"], df["close"])), col_prefix)


def calc_pvr(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.pvr(df["close"], df["volume"])), col_prefix)


# === statistics ===

def calc_entropy(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.entropy(df["close"], length=params[0])), col_prefix)


def calc_skew(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.skew(df["close"], length=params[0])), col_prefix)


def calc_kurtosis(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.kurtosis(df["close"], length=params[0])), col_prefix)


def calc_zscore(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.zscore(df["close"], length=params[0])), col_prefix)


def calc_mad(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.mad(df["close"], length=params[0])), col_prefix)


def calc_quantile(df, params, col_prefix, outputs):
    length, q = params[0], params[1]
    return _series_to_df(_to_series(ta.quantile(df["close"], length=length, q=q)), col_prefix)


# === performance ===

def calc_log_return(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.log_return(df["close"], length=params[0])), col_prefix)


def calc_percent_return(df, params, col_prefix, outputs):
    return _series_to_df(_to_series(ta.percent_return(df["close"], length=params[0])), col_prefix)


# === 2026-09-30 新增:趋势系统 / 多空能量 / 风险回撤 ===
# 注:这里的物理分组只方便阅读,实际归类由 indicators_config.yaml 的 category 决定
# (ichimoku->trend, brar->momentum, drawdown->performance, ui->statistics)。

def calc_ichimoku(df, params, col_prefix, outputs):
    # 一目均衡表,5 输出。pandas-ta 原生列名是 ISA_9/ISB_26/ITS_9/IKS_26/ICS_26,
    # 全部按 outputs 顺序重命名成 <prefix>_<output>,与项目命名规范对齐。
    result = ta.ichimoku(df["high"], df["low"], df["close"])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"ichimoku: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_brar(df, params, col_prefix, outputs):
    # 多空能量比,2 输出(AR=多方能量, BR=空方能量)。需要 open 才能算当日涨跌方向。
    result = ta.brar(df["open"], df["high"], df["low"], df["close"])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"brar: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_drawdown(df, params, col_prefix, outputs):
    # 回撤,3 输出:DD 绝对值 / DD_PCT 百分比 / DD_LOG 对数。
    result = ta.drawdown(df["close"], length=params[0])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"drawdown: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_ui(df, params, col_prefix, outputs):
    # 溃疡指数:回撤深度的平方均值开方,专治「小赚多次、大亏一次」的痛感。
    s = _to_series(ta.ui(df["close"], length=params[0]))
    return _series_to_df(s, col_prefix)


# === 2026-09-30 第二批:动量 / 通道 / 量能 / 日本K线 ===
# 注:这里的物理分组只方便阅读,实际归类由 indicators_config.yaml 的 category 决定。

def calc_stc(df, params, col_prefix, outputs):
    # Schaff 趋势周期。3 输出: stc(主线, 有界 0~100) / macd(中间量) / stoch(随机量)。
    result = ta.stc(df["close"])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"stc: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_lrsi(df, params, col_prefix, outputs):
    # Laguerre RSI:用四级滤波逼近 RSI,平滑且几乎不延迟。有界 [0,100]。
    return _series_to_df(_to_series(ta.lrsi(df["close"], length=params[0])), col_prefix)


def calc_bias(df, params, col_prefix, outputs):
    # 乖离率:(收盘 - 均线) / 均线。A股短线常用。
    return _series_to_df(_to_series(ta.bias(df["close"], length=params[0])), col_prefix)


def calc_accbands(df, params, col_prefix, outputs):
    # 加速带:上下轨 + 中轨。带宽收缩后常预示突破。
    result = ta.accbands(df["high"], df["low"], df["close"], length=params[0])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"accbands: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_vwmacd(df, params, col_prefix, outputs):
    # 成交量加权 MACD:把成交量塞进 MACD 的加权,放大量能的影响。
    result = ta.vwmacd(df["close"], df["volume"],
                       fast=params[0], slow=params[1], signal=params[2])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"vwmacd: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


def calc_vosc(df, params, col_prefix, outputs):
    # 成交量振荡:短期/长期成交量均线的差。量能见顶回落的常用信号。
    # 注意 ta.vosc 返回的是 Series 而不是 DataFrame。
    s = _to_series(ta.vosc(df["volume"], fast=params[0], slow=params[1]))
    return _series_to_df(s, col_prefix)


def calc_ha(df, params, col_prefix, outputs):
    # Heikin-Ashi 日本K线,4 输出(开/高/低/收)。平滑掉跳空,趋势更干净,
    # 代价是拐点滞后 —— 适合看方向,不适合看精确买卖点。
    result = ta.ha(df["open"], df["high"], df["low"], df["close"])
    df_out = _to_dataframe(result)
    if df_out.shape[1] != len(outputs):
        raise ValueError(f"ha: expected {len(outputs)}, got {df_out.shape[1]}")
    return _df_rename_cols(df_out, [f"{col_prefix}_{o}" for o in outputs])


# === zettaranc (zettaranc 战法专用指标) ===

# 白线: EMA(EMA(C, 10), 10)
def calc_zg_white(df, params, col_prefix, outputs):
    length = params[0]
    s = ta.ema(ta.ema(df["close"], length=length), length=length)
    return _series_to_df(_to_series(s), col_prefix)


# 黄线 / 大哥线: (MA14+MA28+MA57+MA114)/4
def calc_dg_yellow(df, params, col_prefix, outputs):
    base = params[0]
    ma_sum = (
        ta.sma(df["close"], length=base)        # MA14
        + ta.sma(df["close"], length=base * 2)  # MA28
        + ta.sma(df["close"], length=base * 4)  # MA57(≈ base*4)
        + ta.sma(df["close"], length=base * 8)  # MA114(≈ base*8)
    )
    yellow = ma_sum / 4.0
    return _series_to_df(_to_series(yellow), col_prefix)


# BBI 多空线: (MA3+MA6+MA12+MA24)/4
def calc_bbi(df, params, col_prefix, outputs):
    bbi = (
        ta.sma(df["close"], length=3)
        + ta.sma(df["close"], length=6)
        + ta.sma(df["close"], length=12)
        + ta.sma(df["close"], length=24)
    ) / 4.0
    return _series_to_df(_to_series(bbi), col_prefix)


# 砖型图 brick_value: (close - open) / (high - low)  — [-1, +1]
#  +1: 实体大阳线 (close=high,open=low)
#   0: 十字星
#  -1: 实体大阴线 (close=low,open=high)
def calc_brick_value(df, params, col_prefix, outputs):
    rng = df["high"] - df["low"]
    body = df["close"] - df["open"]
    brick = body / rng.replace(0, pd.NA)
    return _series_to_df(brick, col_prefix)


# 单针下 20 RSL (Relative Strength Level)
# 短/长期 RSL = N 日涨幅百分位 (0-100,值越高越强)
def calc_rsl_short(df, params, col_prefix, outputs):
    length = params[0]
    pct = df["close"].pct_change(periods=length) * 100
    # 用 pandas rolling rank 估百分位(只用自身 N 日)
    rsl = pct.rolling(length * 5, min_periods=length).rank(pct=True) * 100
    return _series_to_df(rsl, col_prefix)

def calc_rsl_long(df, params, col_prefix, outputs):
    length = params[0]
    pct = df["close"].pct_change(periods=length) * 100
    rsl = pct.rolling(length * 5, min_periods=length).rank(pct=True) * 100
    return _series_to_df(rsl, col_prefix)



# === dispatch ===

CALC_FUNCS = {
    "kdj": calc_kdj, "kc": calc_kc, "cmf": calc_cmf, "vwap": calc_vwap,
    "hma": calc_hma, "alma": calc_alma, "vidya": calc_vidya, "rma": calc_rma,
    "zlma": calc_zlma, "mcgd": calc_mcgd, "fwma": calc_fwma, "hwma": calc_hwma,
    "jma": calc_jma, "pwma": calc_pwma, "swma": calc_swma, "ssf": calc_ssf,
    "sinwma": calc_sinwma,
    "stochf": calc_stochf, "er": calc_er, "eri": calc_eri, "fisher": calc_fisher,
    "qqe": calc_qqe, "rsx": calc_rsx, "smi": calc_smi, "dm": calc_dm,
    "dpo": calc_dpo, "vortex": calc_vortex, "supertrend": calc_supertrend,
    "chop": calc_chop, "inertia": calc_inertia, "decay": calc_decay,
    "emv": calc_emv, "eom": calc_eom, "kvo": calc_kvo, "aobv": calc_aobv,
    "vfi": calc_vfi, "wad": calc_wad, "pvr": calc_pvr,
    "entropy": calc_entropy, "skew": calc_skew, "kurtosis": calc_kurtosis,
    "zscore": calc_zscore, "mad": calc_mad, "quantile": calc_quantile,
    "log_return": calc_log_return, "percent_return": calc_percent_return,
    "zg_white": calc_zg_white, "dg_yellow": calc_dg_yellow, "bbi": calc_bbi,
    "brick_value": calc_brick_value,
    "rsl_short": calc_rsl_short, "rsl_long": calc_rsl_long,
    "ichimoku": calc_ichimoku, "brar": calc_brar,
    "drawdown": calc_drawdown, "ui": calc_ui,
    "stc": calc_stc, "lrsi": calc_lrsi, "bias": calc_bias,
    "accbands": calc_accbands, "vwmacd": calc_vwmacd,
    "vosc": calc_vosc, "ha": calc_ha,
}



def is_pandas_ta_supported(category: str, name: str) -> bool:
    return name in CALC_FUNCS


def calc_indicator(df: pd.DataFrame, category: str, name: str, params,
                   outputs: list[str] | None = None,
                   col_prefix: str | None = None) -> pd.DataFrame:
    if col_prefix is None:
        col_prefix = f"{category}_{name}"
    if outputs is None:
        outputs = []
    fn = CALC_FUNCS[name]
    return fn(df, params, col_prefix, outputs)


if __name__ == "__main__":
    from .loader import load_one
    df = load_one("601398.SH")
    print(f"loaded: {len(df)} rows")
    for cat, name, args, outs in [
        ("momentum", "kdj", [9, 3], ["k", "d", "j"]),
        ("momentum", "qqe", [14, 5], ["qqe", "rsima", "long", "short", "b_l", "b_s", "diff"]),
        ("trend", "supertrend", [10, 3.0], ["trend", "direction", "long", "short"]),
        ("volume", "aobv", [5, 12], ["obv", "min", "max", "ema4", "ema12", "lr", "sr"]),
    ]:
        try:
            r = calc_indicator(df, cat, name, args, outs)
            print(f"  {cat}.{name}: cols={list(r.columns)}")
        except Exception as e:
            print(f"  {cat}.{name}: ERROR {type(e).__name__}: {e}")
