"""paths.py — 项目内所有本地路径的唯一来源。

设计原则：**代码里不出现任何绝对路径**。所有路径都从这里解析，
使用者通过环境变量覆盖即可，无需改代码。

    FUYAO_HOME              数据工作区根目录（存放全部 *.duckdb）
                           默认 ~/.hithink-finance
    FUYAO_MARKET_DB         行情库（raw_* 行情表 + v_daily_qfq 视图）
    FUYAO_INDICATORS_DB     指标库（v_indicators_daily 宽表）
    FUYAO_INDICATORS_CONFIG 指标配置文件

若使用非 editable 安装（pip install . 而非 pip install -e .），
indicators_config.yaml 不会随包分发，请用 FUYAO_INDICATORS_CONFIG 显式指定。
"""

from __future__ import annotations

import os
from pathlib import Path

# 本文件所在目录即项目根（editable 安装时为源码目录）
_PROJECT_ROOT = Path(__file__).resolve().parent


def _env_path(name: str, default: Path) -> Path:
    """读环境变量并展开 ~，未设置时返回默认值。"""
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


# --- 数据工作区 ---------------------------------------------------------------

#: 数据工作区根目录。所有 *.duckdb 都在这里。
FUYAO_HOME = _env_path("FUYAO_HOME", Path.home() / ".hithink-finance")

#: 行情库。指标引擎从这里读日线 OHLCV。
MARKET_DB = _env_path("FUYAO_MARKET_DB", FUYAO_HOME / "market.duckdb")

#: 指标库。计算结果写到这里。
INDICATORS_DB = _env_path("FUYAO_INDICATORS_DB", FUYAO_HOME / "indicators.duckdb")

# --- 项目内文件 ---------------------------------------------------------------

#: 指标配置。列清单、参数、后端选择全部由此驱动。
INDICATORS_CONFIG = _env_path(
    "FUYAO_INDICATORS_CONFIG", _PROJECT_ROOT / "indicators_config.yaml"
)
