"""indicators_schema.py — 从 indicators_config.yaml 生成 duckdb CREATE TABLE

列命名规范:
  - 单输出:       <category>_<name>_<param_slug>
                   例: momentum_rsi_14
  - 多输出:       <category>_<name>_<param_slug>_<output>
                   例: volatility_bbands_20_2_0_upper
                        momentum_macd_12_26_9_hist
  - CDL 形态:    candles_cdl_<name>_0
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from paths import INDICATORS_CONFIG

# talib 的 61 个 CDL 函数名 (talib.get_functions() 验证)
CDL_PATTERNS = [
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


def _param_to_slug(params: Any) -> str:
    if isinstance(params, (list, tuple)):
        return "_".join(str(p).replace(".", "_") for p in params)
    if isinstance(params, dict):
        return "_".join(f"{k}_{v}".replace(".", "_") for k, v in sorted(params.items()))
    if params == {}:
        return ""
    return str(params)


def _sanitize(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9_]", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def expand_columns(cfg: dict) -> list[tuple[str, str]]:
    """[(column_name, indicator_id), ...]

    indicator_id: "<category>:<name>:<param_slug>[:<output>]"
    跳过 metadata 和 candles.all_cdl.
    """
    cols: list[tuple[str, str]] = []
    skip_top = {"metadata"}
    skip_inner = {"all_cdl"}

    for category, indicators in cfg.items():
        if category in skip_top or not isinstance(indicators, dict):
            continue
        for iname, idef in indicators.items():
            if iname in skip_inner:
                continue
            if not isinstance(idef, dict) or not idef.get("enabled", False):
                continue
            params_list = idef.get("params", [{}])
            outputs = idef.get("outputs")
            for params in params_list:
                slug = _param_to_slug(params) if params else ""
                base = f"{_sanitize(category)}_{_sanitize(iname)}_{slug}".rstrip("_")
                if outputs:
                    for out_name in outputs:
                        col = f"{base}_{_sanitize(out_name)}"
                        ind_id = f"{category}:{iname}:{slug}:{out_name}"
                        cols.append((col, ind_id))
                else:
                    ind_id = f"{category}:{iname}:{slug}"
                    cols.append((base, ind_id))
    return cols


def expand_cdl_columns() -> list[tuple[str, str]]:
    return [
        (f"candles_cdl_{_sanitize(c[3:].lower())}_0", f"candles:cdl:{c}")
        for c in CDL_PATTERNS
    ]


def generate_create_table(cfg: dict) -> str:
    cols = expand_columns(cfg) + expand_cdl_columns()
    lines = [
        "CREATE TABLE IF NOT EXISTS v_indicators_daily (",
        "    thscode     VARCHAR  NOT NULL,",
        "    date        DATE     NOT NULL,",
        "    backend     VARCHAR  NOT NULL,",
        "    computed_at TIMESTAMP NOT NULL,",
    ]
    for col, _ in cols:
        lines.append(f"    {_sanitize(col)} DOUBLE,")
    lines.append("    PRIMARY KEY (thscode, date)")
    lines.append(");")
    return "\n".join(lines)


def generate_column_indicator_map(cfg: dict) -> dict[str, str]:
    cols = expand_columns(cfg) + expand_cdl_columns()
    return {col: ind_id for col, ind_id in cols}


if __name__ == "__main__":
    cfg = yaml.safe_load(INDICATORS_CONFIG.read_text())
    cols = expand_columns(cfg) + expand_cdl_columns()
    print(f"total columns: {len(cols)}")
    cdl_count = sum(1 for c, _ in cols if c.startswith("candles_cdl_"))
    print(f"  CDL: {cdl_count}")
    print(f"  technical: {len(cols) - cdl_count}")
    print("\nsample multi-output columns:")
    for c, _ in [x for x in cols if any(s in x[0] for s in ("macd_", "bbands_", "stoch_", "aroon_"))][:8]:
        print(f"  {c}")
    print("\nfirst CDL:")
    for c, _ in [x for x in cols if x[0].startswith("candles_")][:3]:
        print(f"  {c}")
