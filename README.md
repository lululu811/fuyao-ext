# fuyao-ext

> **上游数据服务：[同花顺 hithink-finance](https://fuyao.aicubes.cn/)**
>
> 本项目是它的扩展工具，**不提供任何数据**。仓库内不含任何行情、财务或基金数据文件，
> 也不保证上游服务的可用性、条款或价格。所有数据的版权归同花顺所有，需自行申请 API Key。
> 详见 [`docs/data-sources.md`](docs/data-sources.md)。

A股本地数据仓库的**数据契约 + 采集抽象 + 指标引擎**。

一句话说明它做什么：

> 任何能提供「证券标识 + 日线 OHLCV + 复权因子」的数据源，都能接进同一套数据契约，
> 跑出同一套 264 列指标引擎。

---

## 这是什么，不是什么

| | |
|---|---|
| ✅ 是 | 7 个 DuckDB 数据域的表结构（77 张表 + 41 个视图） |
| ✅ 是 | 采集层抽象：一个 `Ingestor` 协议 + 一个上游参考实现 |
| ✅ 是 | 指标引擎：配置驱动的 264 列宽表，含双后端自动降级、加列回填、写后校验闸门 |
| ❌ 不是 | 一个数据包 —— **本仓库一行数据都没有** |
| ❌ 不是 | 同花顺官方客户端 —— 那个东西是他们的，我们只是调用公开 API |
| ❌ 不是 | 交易策略 —— 指标引擎公开，策略层私有 |

## 项目状态

**⚠️ Phase 1 完成，仍不可端到端运行。** 指标引擎已迁入并通过 import 与语法校验，
依赖改造与路径参数化已完成；但采集层（Phase 3）尚未实现，因此**目前没有数据可供计算**。

| 阶段 | 内容 | 状态 |
|---|---|---|
| 0 | 仓库骨架、许可、依赖清单、决策记录 | ✅ |
| 1 | 指标引擎迁入、依赖改造、路径参数化 | ✅ |
| 2 | 数据契约 DDL 导出与生成器 | ⬜ |
| 3 | `Ingestor` 协议 + 上游参考实现 | ⬜ |
| 4 | 文档：数据来源说明、字段字典 | 🟡 部分（上游说明已完成，字段映射待补） |
| 5 | CI：DDL 可执行性 / 密钥 / 路径泄漏扫描 | ⬜ |

待决策问题见 [`docs/OPEN_ISSUES.md`](docs/OPEN_ISSUES.md)。

## 目录结构

```
paths.py            所有本地路径的唯一来源（环境变量可覆盖）
indicator/          指标引擎
  compute.py          统一计算 API：config → DataFrame
  adapter_talib.py    TA-Lib 后端（~80 个 calc_*）
  adapter_pandas_ta.py pandas-ta 后端（~65 个 calc_*）
  loader.py           从 market.duckdb 读日线 OHLCV
schema/             数据契约
  indicators_schema.py 从 config 推导列清单并生成 DDL
  *.sql               数据契约 DDL（Phase 2）
ingestors/          采集层
  fuyao/              上游参考实现（Phase 3）
scripts/            CLI 入口
indicators_config.yaml  指标配置：列、参数、后端选择的唯一来源
```

## 路径配置

代码中**不含任何绝对路径**，全部经 `paths.py` 解析：

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| `FUYAO_HOME` | `~/.hithink-finance` | 数据工作区根目录 |
| `FUYAO_MARKET_DB` | `$FUYAO_HOME/market.duckdb` | 行情库 |
| `FUYAO_INDICATORS_DB` | `$FUYAO_HOME/indicators.duckdb` | 指标库 |
| `FUYAO_INDICATORS_CONFIG` | `./indicators_config.yaml` | 指标配置 |

## 安装

```bash
git clone https://github.com/<your-account>/fuyao-ext.git
cd fuyao-ext
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

**TA-Lib 不需要自行编译 C 库。** `ta-lib` 从 0.6 起在 PyPI 提供预编译 wheel，
覆盖 macOS（x86_64 / arm64）与 Linux，`pip install` 即可。
只有在非主流平台或极旧 Python 版本上才可能需要走源码编译。

Python 要求 **3.10+**（指标引擎使用 `X | None` 语法，`pandas-ta-classic` 亦要求 3.10+）。

开发环境实测版本：Python 3.14.7 · pandas 3.0.5 · numpy 2.5.3 · duckdb 1.5.5 ·
ta-lib 0.8.0 · pandas-ta-classic 0.8.33.dev63 · PyYAML 6.0.3

### 凭据

密钥**只从环境变量读取**，仓库内不存放任何凭据：

```bash
export HITHINK_FINANCE_API_KEY="your-key"
```

## 数据契约

本项目的数据模型以**可执行 DDL** 为唯一事实源（见 [ADR-0005](docs/adr/0005-ddl-as-contract-source-of-truth.md)）。
`schema/*.sql` 可直接建库；ER 图、字段字典、表清单等一切文档产物均从它生成，不手工维护。

四层结构：

| 层 | 角色 |
|---|---|
| `raw_*` | 上游数据落地面，字段保持上游语义 |
| `stg_*` | 批量导入中转层。**当前全部为空**，是导入路径的历史残留 |
| `dim_*` | 维度表（当前只有证券目录） |
| `v_*` | 读取面，41 个视图。所有复权、快照取最新、跨表联查逻辑收敛于此 |

跨库通用主键是 `thscode`（同花顺证券标识符）。

> **注意**：现有已建库中未实际创建任何主键约束 —— 建表语句里声明过，
> 但数据是绕开约束批量写入的。因此"DDL 与现存库一致"不能靠约束保证，
> 需要自检脚本比对（见计划 Phase 2）。

## 指标引擎

- **列数由配置推导**，不写死 —— 改 `indicators_config.yaml` 即改 schema
- **双后端自动降级**：TA-Lib 与 pandas-ta-classic，任一可用即可
- **加列回填**：只算差集列，不重算全表
- **结构性 NULL 扫描**：区分「预热期正常为空」与「全表恒空（缺陷）」
- **写后校验闸门**：值域、非空率、预热期豁免
- **回看窗口从配置推导** —— 这套机制曾抓出硬编码窗口小于配置声明周期、
  导致某均线列恒为空两个月的缺陷

264 列分十个列族：重叠、动量、趋势、波动、成交量、周期、统计、绩效、蜡烛形态、自定义。

## 采集层

```
Ingestor（协议）           只认数据契约，不认数据源
   └── fuyao（参考实现）   本项目自行编写，调用上游公开 REST API
```

核心契约只含**证券标识 + 日线 OHLCV + 复权因子**；财报、指数、基金、期货、特色数据为可选能力。

参考实现可被任意其他数据源替换 —— 换一个能产出上述三样东西的源即可。
这一抽象是否真的够通用，**目前尚未被第二个实现验证**。

## 文档

| 文件 | 内容 |
|---|---|
| [`CONTEXT.md`](CONTEXT.md) | 术语表：数据模型、指标层、边界、采集 |
| [`docs/OPEN_SOURCE_PLAN.md`](docs/OPEN_SOURCE_PLAN.md) | 分阶段执行计划 |
| [`docs/data-sources.md`](docs/data-sources.md) | **数据来源说明与字段映射**（Phase 4 填充） |
| [`docs/adr/`](docs/adr/) | 架构决策记录 |
| [`docs/field-dictionary.md`](docs/field-dictionary.md) | 字段字典（生成物，Phase 2） |

### 架构决策记录

| ADR | 决策 |
|---|---|
| [0001](docs/adr/0001-distribute-schema-not-data.md) | 不分发任何数据，只分发数据契约 |
| [0002](docs/adr/0002-exclude-hithink-financial-api.md) | 排除 HiThink-Tech/Financial-API，不 vendor、不再分发 |
| [0003](docs/adr/0003-open-tooling-keep-strategies-private.md) | 工具层完全开源，策略层保留私有 |
| [0004](docs/adr/0004-ingestor-protocol-with-fuyao-reference.md) | 采集层用 Ingestor 抽象，附一个上游参考实现 |
| [0005](docs/adr/0005-ddl-as-contract-source-of-truth.md) | 可执行 DDL 为数据契约唯一事实源 |

## 许可与免责

本仓库的**代码、文档与表结构**以 [MIT License](LICENSE) 发布。

**数据不在授权范围内。** 本项目不分发任何数据文件；使用者通过自己的
API Key 从上游服务获取数据，相关权利与义务由其与上游之间的协议约定。

本项目与同花顺（300033.SZ）无隶属、授权或合作关系。"fuyao" 是其产品名称，
本项目名仅用于准确描述"该服务的一个扩展工具"这一关系。

**投资风险自负。** 本项目是数据与计算工具，不构成任何投资建议。

## 致谢

- **同花顺 hithink-finance** —— 上游数据服务，本项目全部数据来源
- **[TA-Lib](https://github.com/TA-Lib/ta-lib-python)** —— 技术指标基础实现
- **[pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic)** —— 技术指标扩展实现
