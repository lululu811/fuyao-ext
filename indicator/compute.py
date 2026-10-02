"""compute.py — 统一 API

输入: 单只票 OHLCV DataFrame + config
输出: 合并的指标 DataFrame,列名严格对齐 schema

列命名:
  - 单输出:  <category>_<name>_<param_slug>
  - 多输出:  <category>_<name>_<param_slug>_<output>
  - CDL:      candles_cdl_<name>_0
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yaml

from paths import INDICATORS_CONFIG
from schema.indicators_schema import _param_to_slug, _sanitize

from .adapter_pandas_ta import (
    calc_indicator as pandas_ta_calc,
)
from .adapter_pandas_ta import (
    is_pandas_ta_supported,
)
from .adapter_talib import (
    CDL_FUNCS,
    is_talib_supported,
)
from .adapter_talib import (
    calc_cdl_indicator as talib_cdl_calc,
)
from .adapter_talib import (
    calc_indicator as talib_calc,
)


def _load_config() -> dict:
    return yaml.safe_load(INDICATORS_CONFIG.read_text())


def _pick_backend(category: str, name: str, native_lib: str, backend_cfg: str) -> str:
    if backend_cfg == "talib":
        return "talib" if is_talib_supported(category, name) else "pandas_ta"
    if backend_cfg == "pandas_ta":
        return "pandas_ta"
    if native_lib == "talib" and is_talib_supported(category, name):
        return "talib"
    if native_lib == "pandas_ta" and is_pandas_ta_supported(category, name):
        return "pandas_ta"
    if is_talib_supported(category, name):
        return "talib"
    if is_pandas_ta_supported(category, name):
        return "pandas_ta"
    raise ValueError(f"no backend supports {category}/{name}")


def _make_col_prefix(category: str, name: str, params) -> str:
    slug = _param_to_slug(params) if params else ""
    base = f"{_sanitize(category)}_{_sanitize(name)}_{slug}".rstrip("_")
    return base


def _normalize_params(params: Any):
    if isinstance(params, (list, tuple, dict)):
        return params
    return [params]


def compute_one(
    df: pd.DataFrame,
    thscode: str,
    config: dict | None = None,
    drop_na_initial: bool = True,
) -> pd.DataFrame:
    if config is None:
        config = _load_config()

    if df.empty:
        return pd.DataFrame()

    computed_at = datetime.now(timezone.utc)
    out_frames: dict[str, pd.Series] = {}
    backends_used: set[str] = set()

    skip_top = {"metadata", "candles"}
    for category, indicators in config.items():
        if category in skip_top or not isinstance(indicators, dict):
            continue
        for iname, idef in indicators.items():
            if iname == "all_cdl":
                continue
            if not isinstance(idef, dict) or not idef.get("enabled", False):
                continue

            params_list = idef.get("params", [{}])
            if not isinstance(params_list, list):
                params_list = [params_list]
            outputs = idef.get("outputs")
            native_lib = idef.get("native_lib", "talib")
            backend_cfg = idef.get("backend", "auto")

            for params in params_list:
                params = _normalize_params(params)
                backend = _pick_backend(category, iname, native_lib, backend_cfg)
                backends_used.add(backend)
                col_prefix = _make_col_prefix(category, iname, params)
                try:
                    if backend == "talib":
                        r = talib_calc(df, category, iname, params, outputs, col_prefix)
                    else:
                        r = pandas_ta_calc(df, category, iname, params, outputs, col_prefix)
                except Exception as e:
                    print(f"[warn] {thscode} {category}/{iname}{params} failed: {e}")
                    continue
                for col in r.columns:
                    out_frames[col] = r[col]

    # CDL 批量
    candles_cfg = config.get("candles", {}).get("all_cdl", {})
    if candles_cfg.get("enabled", False):
        backends_used.add("talib")
        for cdl_name in CDL_FUNCS:
            try:
                r = talib_cdl_calc(df, cdl_name)
                base = cdl_name[3:].lower()
                col_name = f"candles_cdl_{base}_0"
                out_frames[col_name] = r.iloc[:, 0]
            except Exception as e:
                print(f"[warn] {thscode} CDL {cdl_name} failed: {e}")

    if not out_frames:
        return pd.DataFrame()

    result = pd.DataFrame(out_frames, index=df.index)
    result.insert(0, "thscode", thscode)
    result.insert(1, "date", result.index)
    result.insert(2, "backend", "|".join(sorted(backends_used)))
    result.insert(3, "computed_at", computed_at)

    if drop_na_initial:
        first_valid = result.iloc[:, 4:].dropna(how="all").first_valid_index()
        if first_valid is not None:
            result = result.loc[first_valid:]

    return result.reset_index(drop=True)


if __name__ == "__main__":
    from .loader import load_one
    df = load_one("601398.SH")
    print(f"loaded: {len(df)} rows")
    import time
    t0 = time.time()
    result = compute_one(df, "601398.SH")
    elapsed = time.time() - t0
    print(f"computed: {len(result)} rows × {len(result.columns)} cols in {elapsed:.2f}s")
    print(f"backend: {result['backend'].iloc[0]}")
    print(f"first 8 cols: {list(result.columns[:8])}")
    print(f"last 5 cols: {list(result.columns[-5:])}")
    print("\nsample values (last row):")
    for c in [
        "overlap_sma_20", "overlap_sma_60", "overlap_sma_250",
        "momentum_rsi_14", "momentum_macd_12_26_9_hist",
        "volatility_bbands_20_2_0_middle",
        "volatility_donchian_20_upper", "volatility_donchian_20_middle",
        "volume_obv", "volume_mfi_14",
        "momentum_kdj_9_3_j",
        "candles_cdl_doji_0", "candles_cdl_hammer_0",
    ]:
        if c in result.columns:
            v = result[c].iloc[-1]
            print(f"  {c}: {v if pd.notna(v) else 'NaN'}")
