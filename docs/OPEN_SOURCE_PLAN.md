# fuyao-ext 开源执行计划

> 依据 [ADR-0001](adr/0001-distribute-schema-not-data.md) 至 [ADR-0005](adr/0005-ddl-as-contract-source-of-truth.md)。
> 决策已全部收口，本文件是落地路径。

## 目标形态

一个仓库，三样东西，零数据：

```
fuyao-ext/
├── schema/                 数据契约（可执行 DDL，唯一事实源）
├── ingestors/              采集抽象
│   ├── base.py             Ingestor 协议
│   └── fuyao/              上游参考实现
├── indicator/              指标引擎（config 驱动，264 列）
├── docs/
│   ├── adr/
│   ├── data-sources.md     数据来源说明
│   └── field-dictionary.md （生成物）
├── tests/
├── pyproject.toml
├── LICENSE
└── README.md
```

**核心卖点一句话**：任何能提供「证券标识 + 日线 OHLCV + 复权因子」的数据源都能接进来，
灌进同一套数据契约，跑出同一套 264 列指标引擎。

---

## 关键前提修正：参考实现已有 80%

原以为"采集层要从零重写"，实际不是。

- `~/.hithink-finance/scripts/hfkit.py` + 6 个 `*_db.py`（财报/基金/指数/期货/特色数据）
  是**作者自己写的**，在作者自己的 git 仓里，有 commit 记录。这是可复用的自有资产。
- 唯一真正缺失的是 **`market_db.py`** —— OHLCV 与复权因子的落库，一直由上游的 `marketdb`
  承担（见 [ADR-0002](adr/0002-exclude-hithink-financial-api.md)），作者从未写过。

所以采集层的工作量是**重构 + 补一个模块**，不是重写：

| 工作 | 来源 | 量级 |
|---|---|---|
| 6 个数据域的 Ingestor | 重构自有 `hfkit.py` + `*_db.py` | 中 |
| 行情 + 复权因子 Ingestor | **新写** | 中 |
| 协议抽象层 | 新写 | 小 |

---

## Phase 0 — 骨架

- [ ] `git init`，默认分支 `main`
- [ ] `LICENSE`（MIT）
- [ ] `pyproject.toml` —— **两个现有仓都没有**，可复现性目前为零
- [ ] `.gitignore`（含 `data/`、`*.duckdb`、`__pycache__/`、`.omc/`、`.bak.*`）
- [ ] `README.md`，**必须在首屏显著位置声明**：
  - 上游数据服务为同花顺 hithink-finance（`fuyao.aicubes.cn`）
  - 本项目不提供任何数据、不保证上游可用性
  - 许可与免责：数据版权归同花顺所有；本项目许可仅覆盖代码
- [ ] 历史处理：两个源仓的 commit 1 均为「建立版本控制基线(此前无 git)」，
      共 5–7 个 commit 覆盖全部历史。**建议 squash 成单条初始提交**，
      否则读者会看到"5 天写完 264 列指标引擎"。

## Phase 1 — 指标引擎迁移（从 `a-stock`）

来源：`/Users/chenlei/007_DB/a-stock`（31 个跟踪文件，git 状态干净）

- [ ] 迁移 `adapter/`、`schema/`、`scripts/`、`indicators_config.yaml`
- [ ] **依赖改造**：现无依赖清单，依赖是 gitignore 掉的 `pandas-ta-classic/` 与
      `ta-lib-python/` 两个本地副本，靠 `add_zettaranc_columns.py:29-33` 手动
      `sys.path` 注入（目录名带连字符，必须显式指到包目录）。改为 `pyproject.toml`
      正常声明依赖
- [ ] **路径参数化**：以下位置硬编码了 `/Users/chenlei/...`，统一走环境变量
      - `adapter/loader.py:24`（`DEFAULT_DB`）
      - `scripts/indicators_sync.py:32-33`
      - `scripts/add_zettaranc_columns.py:41`
      - `scripts/build_indicators.py:23`
      - `scripts/add_indicators.py:45`
      - `scripts/fix_kc_columns.py:39`
      - `strategies/sql/` 下 12 处 `ATTACH '/Users/chenlei/.hithink-finance/...'`
- [ ] **修 RSL 双实现不一致**（发布前必修，属真实缺陷）：
      `adapter/adapter_pandas_ta.py:474-485` 用 `rolling(length*5)`，
      `add_zettaranc_columns.py:122-123` 用固定 15/105 窗口，**两条路径产出不同值**。
      收敛为单一实现
- [ ] 修 `indicators_sync.py:160` 类型标注引用 `pd` 但该文件从未 `import pandas`
      （因 `from __future__ import annotations` 暂不崩，属潜在缺陷）

## Phase 2 — 数据契约 DDL

- [ ] 从现存 7 个 DuckDB 导出全部 **77 张基表 + 41 个视图**的 DDL 到 `schema/*.sql`
- [ ] `stg_*` 三张表全为空，**保留结构但必须在文档中如实标注"当前为空"**，
      不可让其看起来像缺陷
- [ ] 建库时无任何主键约束（DDL 里声明过，但数据绕开约束批量写入），
      需一个自检脚本比对 DDL 与现存库是否一致 —— 约束保证不了这件事
- [ ] 生成器：表清单、ER 图、字段字典均从 DDL 生成（[ADR-0005](adr/0005-ddl-as-contract-source-of-truth.md)）

## Phase 3 — 采集层

- [ ] `ingestors/base.py`：Ingestor 协议。核心契约只含
      **证券标识 + 日线 OHLCV + 复权因子**；财报/指数/基金/期货/特色数据为可选能力
- [ ] `ingestors/fuyao/`：重构自有 `hfkit.py`（凭据加载走仓外 `credentials.env` 的做法保留）
- [ ] **新写**行情 + 复权因子 Ingestor
- [ ] README 提供第二个数据源的接入示例（tushare 或 akshare 任选其一），
      用于证明抽象层不是纸面设计

## Phase 4 — 文档

- [ ] `docs/data-sources.md`：每个数据域的数据来源、上游接口、
      **字段映射关系**（这是"数据来源说明"的实际内容，也是使用者自建 Ingestor 的依据）
- [ ] **`indicators_config.yaml:14-40` 的负面实验记录必须保留并单独成章**：
      第二批 30 个候选中 7 个（23%）被实测否决（MAVP / VP / SAREXT / KST / EFI / CG / RVGI），
      附教训「能算、不报错、值域离谱」。**这是全项目最稀缺的资产，开源界几乎无人记录
      自己试过什么、为什么扔掉。**
- [ ] 声明策略层私有（[ADR-0003](adr/0003-open-tooling-keep-strategies-private.md)）

## Phase 5 — 清理与 CI

- [ ] **确认不迁入**：`strategies/`、`b1.md`、选股 SQL。
      私有仓中的真实资金安排（单笔仓位、分批节奏的具体数字）比战法定义本身更敏感
- [ ] `~/.hithink-finance` 中 **3 个 `.bak.*` 文件当前是被 git 跟踪的**，
      若沿用其历史需剔除
- [ ] 修正文档中已失真的表述（原 `AGENTS.md:5` 声称"无 git 仓库"，而仓库已于 2026-09-30 建立）
- [ ] CI 三件事：
      1. DDL 可执行性校验（干净库中建表成功）
      2. 密钥扫描
      3. 绝对路径泄漏扫描（`/Users/...`）
- [ ] 硬编码 shebang 全部改为 `#!/usr/bin/env python3`

---

## 已核实的干净项（无需处理）

- **无任何硬编码密钥**。两个仓的完整 git 历史中均无 key/token/secret 赋值。
  凭据设计正确：存于仓外 `~/Library/Application Support/hithink-finance/credentials.env`（权限 600）
- 无邮箱、手机号、身份证等直接个人标识
- `logs/`（70 个文件 41 MB）无凭据泄漏
- 指标引擎的核心抽象质量高，是本项目真正的价值所在：
  - 列数由配置推导，不写死
  - 双后端自动降级
  - 加列回填 + 结构性 NULL 扫描
  - **写后校验闸门**（值域 / 非空率 / 预热期豁免）
  - 回看窗口从配置推导 —— 曾借此抓出硬编码窗口小于配置声明周期、
    导致某均线列恒为空两个月的缺陷

## 仍需你确认的

1. **历史是否 squash**（[Phase 0](#phase-0--骨架)）
2. **公开仓归属** —— 个人实名还是组织身份。
   考虑到 `fuyao` 商标进入项目名、且指标引擎署有 `zettaranc` 品牌，
   建议以项目名义而非个人名义发布，避免将个人身份与特定供应商强绑定
3. **参考实现的第二个数据源选 tushare 还是 akshare**
   （tushare 字段更全但需积分，akshare 开箱即用但稳定性差）
