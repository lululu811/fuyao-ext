"""adapter_talib.py — TA-Lib C 库适配器 (全量版)

输入: 单只票的 pandas DataFrame (DatetimeIndex, columns=[open, high, low, close, volume])
输出: 单只票的 pandas DataFrame,列名 = schema 期望的列名
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import talib


def _np(series):
    return series.to_numpy(dtype=np.float64)


def _result_to_df(value, df: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    if isinstance(value, tuple):
        return pd.DataFrame(
            {n: pd.Series(v, index=df.index) for n, v in zip(names, value)},
            index=df.index,
        )
    return pd.DataFrame({names[0]: pd.Series(value, index=df.index)}, index=df.index)


# === 单输出 (OHLCV 各种组合) ===

def calc_sma(df, period): return talib.SMA(_np(df["close"]), timeperiod=period)
def calc_ema(df, period): return talib.EMA(_np(df["close"]), timeperiod=period)
def calc_wma(df, period): return talib.WMA(_np(df["close"]), timeperiod=period)
def calc_dema(df, period): return talib.DEMA(_np(df["close"]), timeperiod=period)
def calc_tema(df, period): return talib.TEMA(_np(df["close"]), timeperiod=period)
def calc_trima(df, period): return talib.TRIMA(_np(df["close"]), timeperiod=period)
def calc_kama(df, period): return talib.KAMA(_np(df["close"]), timeperiod=period)
def calc_t3(df, period): return talib.T3(_np(df["close"]), timeperiod=period)
def calc_ht_trendline(df): return talib.HT_TRENDLINE(_np(df["close"]))
def calc_rsi(df, period): return talib.RSI(_np(df["close"]), timeperiod=period)
def calc_willr(df, period): return talib.WILLR(_np(df["high"]), _np(df["low"]), _np(df["close"]), timeperiod=period)
def calc_cci(df, period): return talib.CCI(_np(df["high"]), _np(df["low"]), _np(df["close"]), timeperiod=period)
def calc_adx(df, period): return talib.ADX(_np(df["high"]), _np(df["low"]), _np(df["close"]), timeperiod=period)
def calc_adxr(df, period): return talib.ADXR(_np(df["high"]), _np(df["low"]), _np(df["close"]), timeperiod=period)
def calc_dx(df, period): return talib.DX(_np(df["high"]), _np(df["low"]), _np(df["close"]), timeperiod=period)
def calc_atr(df, period): return talib.ATR(_np(df["high"]), _np(df["low"]), _np(df["close"]), timeperiod=period)
def calc_natr(df, period): return talib.NATR(_np(df["high"]), _np(df["low"]), _np(df["close"]), timeperiod=period)
def calc_trange(df): return talib.TRANGE(_np(df["high"]), _np(df["low"]), _np(df["close"]))
def calc_obv(df): return talib.OBV(_np(df["close"]), _np(df["volume"]))
def calc_ad(df): return talib.AD(_np(df["high"]), _np(df["low"]), _np(df["close"]), _np(df["volume"]))
def calc_mfi(df, period): return talib.MFI(_np(df["high"]), _np(df["low"]), _np(df["close"]), _np(df["volume"]), timeperiod=period)
def calc_mom(df, period): return talib.MOM(_np(df["close"]), timeperiod=period)
def calc_roc(df, period): return talib.ROC(_np(df["close"]), timeperiod=period)
def calc_rocp(df, period): return talib.ROCP(_np(df["close"]), timeperiod=period)
def calc_rocr(df, period): return talib.ROCR(_np(df["close"]), timeperiod=period)
def calc_trix(df, period): return talib.TRIX(_np(df["close"]), timeperiod=period)
def calc_cmo(df, period): return talib.CMO(_np(df["close"]), timeperiod=period)
def calc_qstick(df, period): return talib.QSTICK(_np(df["open"]), _np(df["close"]), timeperiod=period)
def calc_beta(df, period): return talib.BETA(_np(df["high"]), _np(df["low"]), timeperiod=period)
def calc_correl(df, period): return talib.CORREL(_np(df["high"]), _np(df["low"]), timeperiod=period)
def calc_linearreg(df, period): return talib.LINEARREG(_np(df["close"]), timeperiod=period)
def calc_linearreg_angle(df, period): return talib.LINEARREG_ANGLE(_np(df["close"]), timeperiod=period)
def calc_linearreg_intercept(df, period): return talib.LINEARREG_INTERCEPT(_np(df["close"]), timeperiod=period)
def calc_linearreg_slope(df, period): return talib.LINEARREG_SLOPE(_np(df["close"]), timeperiod=period)
def calc_tsf(df, period): return talib.TSF(_np(df["close"]), timeperiod=period)
def calc_stddev(df, period): return talib.STDDEV(_np(df["close"]), timeperiod=period, nbdev=1)
def calc_var(df, period): return talib.VAR(_np(df["close"]), timeperiod=period, nbdev=1)
def calc_ht_dcperiod(df): return talib.HT_DCPERIOD(_np(df["close"]))
def calc_ht_dcphase(df): return talib.HT_DCPHASE(_np(df["close"]))
def calc_ht_trendmode(df): return talib.HT_TRENDMODE(_np(df["close"]))
def calc_pvt(df): return talib.PVT(_np(df["close"]), _np(df["volume"]))
def calc_nvi(df): return talib.NVI(_np(df["close"]), _np(df["volume"]))
def calc_pvi(df): return talib.PVI(_np(df["close"]), _np(df["volume"]))


# === 多输出 ===

def calc_macd(df, fast, slow, signal):
    return talib.MACD(_np(df["close"]), fastperiod=fast, slowperiod=slow, signalperiod=signal)

def calc_stoch(df, k_period, d_period, smooth_k):
    return talib.STOCH(
        _np(df["high"]), _np(df["low"]), _np(df["close"]),
        fastk_period=k_period, slowk_matype=0,
        slowk_period=smooth_k, slowd_period=d_period, slowd_matype=0,
    )

def calc_stochrsi(df, period):
    return talib.STOCHRSI(_np(df["close"]), timeperiod=period, fastk_period=14, fastd_period=14, fastd_matype=0)

def calc_aroon(df, period):
    return talib.AROON(_np(df["high"]), _np(df["low"]), timeperiod=period)  # (down, up)

def calc_bbands(df, period, std):
    return talib.BBANDS(_np(df["close"]), timeperiod=period, nbdevup=std, nbdevdn=std, matype=0)

def calc_donchian(df, period):
    return talib.DONCHIAN(_np(df["high"]), _np(df["low"]), timeperiod=period)

def calc_adosc(df, fast, slow):
    return talib.ADOSC(_np(df["high"]), _np(df["low"]), _np(df["close"]), _np(df["volume"]), fastperiod=fast, slowperiod=slow)

def calc_psar(df):
    return talib.SAR(_np(df["high"]), _np(df["low"]), acceleration=0.02, maximum=0.2)

def calc_mama(df):
    return talib.MAMA(_np(df["close"]))

def calc_apo(df, fast, slow):
    return talib.APO(_np(df["close"]), fastperiod=fast, slowperiod=slow)

def calc_ppo(df, fast, slow):
    return talib.PPO(_np(df["close"]), fastperiod=fast, slowperiod=slow)

def calc_tsi(df, fast, slow):
    return talib.TSI(_np(df["close"]), fast, slow)

def calc_ht_phasor(df):
    return talib.HT_PHASOR(_np(df["close"]))

def calc_ht_sine(df):
    return talib.HT_SINE(_np(df["close"]))


# === 61 CDL ===

CDL_FUNCS = [
    "CDL2CROWS", "CDL3BLACKCROWS", "CDL3INSIDE", "CDL3LINESTRIKE",
    "CDL3OUTSIDE", "CDL3STARSINSOUTH", "CDL3WHITESOLDIERS", "CDLABANDONEDBABY",
    "CDLADVANCEBLOCK", "CDLBELTHOLD", "CDLBREAKAWAY", "CDLCLOSINGMARUBOZU",
    "CDLCONCEALBABYSWALL", "CDLCOUNTERATTACK", "CDLDARKCLOUDCOVER",
    "CDLDOJI", "CDLDOJISTAR", "CDLDRAGONFLYDOJI", "CDLENGULFING",
    "CDLEVENINGDOJISTAR", "CDLEVENINGSTAR", "CDLGAPSIDESIDEWHITE",
    "CDLGRAVESTONEDOJI", "CDLHAMMER", "CDLHANGINGMAN", "CDLHARAMI",
    "CDLHARAMICROSS", "CDLHIGHWAVE", "CDLHIKKAKE", "CDLHIKKAKEMOD",
    "CDLHOMINGPIGEON", "CDLIDENTICAL3CROWS", "CDLINNECK",
    "CDLINVERTEDHAMMER", "CDLKICKING", "CDLKICKINGBYLENGTH",
    "CDLLADDERBOTTOM", "CDLLONGLEGGEDDOJI", "CDLLONGLINE",
    "CDLMARUBOZU", "CDLMATCHINGLOW", "CDLMATHOLD", "CDLMORNINGDOJISTAR",
    "CDLMORNINGSTAR", "CDLONNECK", "CDLPIERCING", "CDLRICKSHAWMAN",
    "CDLRISEFALL3METHODS", "CDLSEPARATINGLINES", "CDLSHOOTINGSTAR",
    "CDLSHORTLINE", "CDLSPINNINGTOP", "CDLSTALLEDPATTERN",
    "CDLSTICKSANDWICH", "CDLTAKURI", "CDLTASUKIGAP", "CDLTHRUSTING",
    "CDLTRISTAR", "CDLUNIQUE3RIVER", "CDLUPSIDEGAP2CROWS",
    "CDLXSIDEGAP3METHODS",
]


def calc_cdl(df, cdl_name):
    fn = getattr(talib, cdl_name)
    return fn(_np(df["open"]), _np(df["high"]), _np(df["low"]), _np(df["close"]))


# === 2026-09-30 新增:成交量加权均价 ===

def calc_vwma(df, period):
    # VWMA = 成交量加权均价。与 VWAP 的区别: VWAP 是会话内累积量加权,
    # VWMA 是滚动 N 日窗口重算 —— 成本线体系里的中长周期那条线。
    return talib.VWMA(_np(df["close"]), _np(df["volume"]), timeperiod=period)


# SAREXT 曾在 2026-09-30 评估过,结论是不用: 该 build 的 talib.SAREXT 输出会
# 发散 —— 600519.SH(价格在 1151~1772)上 50%+ 的取值为负,末值 -1301,且对
# startValue 取 0.02 / 0 / 首收盘价 三种变体结果完全一致,不是参数语义问题。
# 对比之下 calc_psar 走 talib.SAR,末值 1277、零负值,是正常的。
# SAREXT 相对 PSAR 的唯一增量是「多空两侧用不同加速上限」,边际收益不足以
# 承担往 16GB 宽表里写一列会跑到 -1806 的数据的风险,故不启用。


# === 2026-09-30 第二批:动量 / 波动 / 量能 ===

def calc_ultosc(df, p1, p2, p3):
    # 终极振荡器:7/14/28 三个周期超买超卖占比的加权。天然有界 [0,100]。
    return talib.ULTOSC(_np(df["high"]), _np(df["low"]), _np(df["close"]),
                        p1, p2, p3)


def calc_ao(df, fast, slow):
    # Awesome 振荡:5 期中位价 - 34 期中位价。
    return talib.AO(_np(df["high"]), _np(df["low"]),
                    fastperiod=fast, slowperiod=slow)


def calc_coppock(df, wma, roc1, roc2):
    # 库普考克:长期动量,周线月线 ROC 取平均再套 WMA,专判牛熊转换。
    return talib.COPPOCK(_np(df["close"]), wmaperiod=wma,
                         roc1period=roc1, roc2period=roc2)


def calc_rvi(df, period, stddev):
    # 相对波动率指数。stddev 取 252(一年)才有金融含义。
    return talib.RVI(_np(df["close"]), timeperiod=period, stddevperiod=stddev)


def calc_vhf(df, period):
    # 垂直水平过滤:用 (H+L)/2 而不是收盘价 —— 这是 TA-Lib 的签名要求,
    # 传 close 会算错。值域有界 [0,1],接近 1 = 趋势性强。
    mid = ((df["high"] + df["low"]) / 2.0).to_numpy(dtype=np.float64)
    return talib.VHF(mid, timeperiod=period)


# === 分发 ===

# (category, name) -> (calc_func, param_keys)
TALIB_REGISTRY = {
    ("overlap", "sma"): (calc_sma, ["period"]),
    ("overlap", "ema"): (calc_ema, ["period"]),
    ("overlap", "wma"): (calc_wma, ["period"]),
    ("overlap", "dema"): (calc_dema, ["period"]),
    ("overlap", "tema"): (calc_tema, ["period"]),
    ("overlap", "trima"): (calc_trima, ["period"]),
    ("overlap", "kama"): (calc_kama, ["period"]),
    ("overlap", "t3"): (calc_t3, ["period"]),
    ("overlap", "mama"): (calc_mama, []),
    ("overlap", "ht_trendline"): (calc_ht_trendline, []),
    ("overlap", "vwma"): (calc_vwma, ["period"]),
    ("momentum", "ultosc"): (calc_ultosc, ["p1", "p2", "p3"]),
    ("momentum", "ao"): (calc_ao, ["fast", "slow"]),
    ("momentum", "coppock"): (calc_coppock, ["wma", "roc1", "roc2"]),
    ("momentum", "rvi"): (calc_rvi, ["period", "stddev"]),
    ("volatility", "vhf"): (calc_vhf, ["period"]),
    ("momentum", "rsi"): (calc_rsi, ["period"]),
    ("momentum", "macd"): (calc_macd, ["fast", "slow", "signal"]),
    ("momentum", "stoch"): (calc_stoch, ["k_period", "d_period", "smooth_k"]),
    ("momentum", "stochrsi"): (calc_stochrsi, ["period"]),
    ("momentum", "willr"): (calc_willr, ["period"]),
    ("momentum", "cci"): (calc_cci, ["period"]),
    ("momentum", "adx"): (calc_adx, ["period"]),
    ("momentum", "adxr"): (calc_adxr, ["period"]),
    ("momentum", "aroon"): (calc_aroon, ["period"]),
    ("momentum", "mom"): (calc_mom, ["period"]),
    ("momentum", "roc"): (calc_roc, ["period"]),
    ("momentum", "rocp"): (calc_rocp, ["period"]),
    ("momentum", "rocr"): (calc_rocr, ["period"]),
    ("momentum", "trix"): (calc_trix, ["period"]),
    ("momentum", "tsi"): (calc_tsi, ["fast", "slow"]),
    ("momentum", "cmo"): (calc_cmo, ["period"]),
    ("momentum", "apo"): (calc_apo, ["fast", "slow"]),
    ("momentum", "ppo"): (calc_ppo, ["fast", "slow"]),
    ("trend", "psar"): (calc_psar, []),
    ("trend", "adx"): (calc_adx, ["period"]),
    ("trend", "aroon"): (calc_aroon, ["period"]),
    ("trend", "dx"): (calc_dx, ["period"]),
    ("trend", "qstick"): (calc_qstick, ["period"]),
    ("volatility", "bbands"): (calc_bbands, ["period", "std"]),
    ("volatility", "atr"): (calc_atr, ["period"]),
    ("volatility", "natr"): (calc_natr, ["period"]),
    ("volatility", "donchian"): (calc_donchian, ["period"]),
    ("volatility", "trange"): (calc_trange, []),
    ("volume", "obv"): (calc_obv, []),
    ("volume", "ad"): (calc_ad, []),
    ("volume", "adosc"): (calc_adosc, ["fast", "slow"]),
    ("volume", "mfi"): (calc_mfi, ["period"]),
    ("volume", "pvt"): (calc_pvt, []),
    ("volume", "nvi"): (calc_nvi, []),
    ("volume", "pvi"): (calc_pvi, []),
    ("cycles", "ht_dcperiod"): (calc_ht_dcperiod, []),
    ("cycles", "ht_dcphase"): (calc_ht_dcphase, []),
    ("cycles", "ht_phasor"): (calc_ht_phasor, []),
    ("cycles", "ht_sine"): (calc_ht_sine, []),
    ("cycles", "ht_trendmode"): (calc_ht_trendmode, []),
    ("statistics", "beta"): (calc_beta, ["period"]),
    ("statistics", "correl"): (calc_correl, ["period"]),
    ("statistics", "linearreg"): (calc_linearreg, ["period"]),
    ("statistics", "linearreg_angle"): (calc_linearreg_angle, ["period"]),
    ("statistics", "linearreg_intercept"): (calc_linearreg_intercept, ["period"]),
    ("statistics", "linearreg_slope"): (calc_linearreg_slope, ["period"]),
    ("statistics", "tsf"): (calc_tsf, ["period"]),
    ("statistics", "stddev"): (calc_stddev, ["period"]),
    ("statistics", "var"): (calc_var, ["period"]),
}


def is_talib_supported(category: str, name: str) -> bool:
    return (category, name) in TALIB_REGISTRY


def calc_indicator(df: pd.DataFrame, category: str, name: str, params,
                   outputs: list[str] | None = None,
                   col_prefix: str | None = None) -> pd.DataFrame:
    calc, keys = TALIB_REGISTRY[(category, name)]
    if not keys:
        kw = {}
    elif isinstance(params, dict):
        kw = {k: params[k] for k in keys if k in params}
    else:
        kw = {keys[i]: params[i] for i in range(min(len(keys), len(params)))}
    value = calc(df, **kw) if kw else calc(df)

    if isinstance(value, tuple):
        if outputs:
            names = [f"{col_prefix}_{o}" if col_prefix else o for o in outputs]
        else:
            names = [f"{col_prefix}_{i}" if col_prefix else f"v_{i}" for i in range(len(value))]
    else:
        names = [col_prefix if col_prefix else "v"]

    # 特殊修正: AROON (down, up) -> (up, down)
    if (category, name) == ("momentum", "aroon") and outputs == ["aroonup", "aroondown"]:
        value = (value[1], value[0])
    if (category, name) == ("trend", "aroon") and outputs == ["aroonup", "aroondown"]:
        value = (value[1], value[0])

    return _result_to_df(value, df, names)


def calc_cdl_indicator(df: pd.DataFrame, cdl_name: str) -> pd.DataFrame:
    value = calc_cdl(df, cdl_name)
    return _result_to_df(value, df, ["v"])


if __name__ == "__main__":
    from .loader import load_one
    df = load_one("601398.SH")
    print(f"loaded: {len(df)} rows")

    r = calc_indicator(df, "overlap", "sma", [20], col_prefix="overlap_sma_20")
    print(f"SMA_20 cols: {list(r.columns)}, last: {r.iloc[-1, 0]:.4f}")

    r = calc_indicator(df, "momentum", "macd", [12, 26, 9],
                       outputs=["macd", "signal", "hist"],
                       col_prefix="momentum_macd_12_26_9")
    print(f"MACD cols: {list(r.columns)}, hist last: {r.iloc[-1, 2]:.4f}")

    r = calc_indicator(df, "cycles", "ht_phasor", [],
                       outputs=["inphase", "quadrature"],
                       col_prefix="cycles_ht_phasor")
    print(f"HT_PHASOR cols: {list(r.columns)}, last: {r.iloc[-1, 0]:.4f}")
