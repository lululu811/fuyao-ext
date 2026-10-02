# fuyao-ext 开源执行计划

> 依据 [ADR-0001](../docs/adr/0001-distribute-schema-not-data.md) 至 [ADR-0005](../docs/adr/0005-ddl-as-contract-source-of-truth.md)。
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
  承担（见 [ADR-0002](../docs/adr/0002-exclude-hithink-financial-api.md)），作者从未写过。

所以采集层的工作量是**重构 + 补一个模块**，不是重写：

| 工作 | 来源 | 量级 |
|---|---|---|
| 6 个数据域的 Ingestor | 重构自有 `hfkit.py` + `*_db.py` | 中 |
| 行情 + 复权因子 Ingestor | **新写** | 中 |
| 协议抽象层 | 新写 | 小 |

---

## Phase 0 — 骨架 ✅

- [x] `git init`，默认分支 `main`
- [x] `LICENSE`（MIT + DATA NOTICE：许可仅覆盖代码，数据不在授权范围）
- [x] `pyproject.toml` —— 依赖清单由实际 import 扫描得出
- [x] `.gitignore`（数据 / 凭据 / vendored 依赖 / 私有层四类拦截）
- [x] `README.md`，首屏声明上游数据服务为同花顺 hithink-finance
- [x] 历史 squash 成单条初始提交

## Phase 1 — 指标引擎迁移（从 `a-stock`）✅

来源：作者的私有仓 `a-stock`。共迁入 14 个文件、3,626 行。

- [x] 迁移 `adapter/` → **`indicator/`**（改名：`adapter` 对开源项目是误导名，
      实际是引擎核心）、`schema/indicators_schema.py`、`scripts/*.py`、
      `indicators_config.yaml`
- [x] **排除私有层**：`strategies/`（11 个文件）、`b1.md`、
      `scripts/b1_screen.sql`（B1 选股模型 SQL，属策略层）
- [x] **依赖改造**：移除全部 `sys.path` 隐式路径注入（含
      `sys.path.insert(ROOT / "pandas-ta-classic")`），改为 `pyproject.toml` 声明
- [x] **路径参数化**：新增 `paths.py` 作为唯一来源，18 处硬编码路径全部替换，
      7 个环境变量可覆盖
- [x] 修 `indicators_sync.py:160` 类型标注引用 `pd` 但未 import
- [x] 补 `schema/__init__.py`（上游缺，靠隐式 namespace package 才能 import）
- [x] 验证：全部文件 `compileall` 通过；6 个脚本 import 链全通
- [x] `_derive_lookback()` 实测推导 252 bar → 455 自然日

### ⚠️ 未能完成：RSL 双实现收敛

原计划记为"两条路径产出不同值"。**经核实该判断有误** ——
`length*5` 在 length=3/21 时恰好等于脚本的固定窗口 15/105，`min_periods` 也一致，
**数值完全等价**。

真实问题是**产出两套列名**（`zettaranc_rsl_short_3`/`_long_21` 与
`zettaranc_rsl_rank_15`/`_rank_105`），且前者正是被判定为误导的旧名。
收敛需要改函数签名，且会影响线上 10,349,853 行表的 schema，
因此**未擅自改动**，转为待决策项 → [`OPEN_ISSUES.md`](OPEN_ISSUES.md) 第 1 条。

## Phase 2 — 数据契约 DDL

- [x] 从现存 7 个 DuckDB 导出全部 **62 张基表 + 41 个视图**的 DDL 到 `schema/*.sql`
- [x] `stg_*` 三张表全为空，**保留结构但必须在文档中如实标注"当前为空"**，
      不可让其看起来像缺陷 → `schema/README.md`
- [x] 自检脚本 `scripts/export_schema.py --check`：干净内存库执行 DDL 后，
      与现存库逐对象逐列比对。
      **更正**：62 张表中 59 张**确有** PRIMARY KEY 声明（此前误记为"零主键"，
      起因是查了 `duckdb_constraints()`，而 DuckDB 不把约束存进 catalog，
      只在 `duckdb_tables().has_primary_key` 留布尔标记）。仅 3 张空的 `stg_*` 无 PK。
- [x] 生成器：字段字典（`scripts/gen_field_dictionary.py` → 62 表 846 列）、
      ER 图（`scripts/gen_er_diagram.py` → Mermaid，GitHub 原生渲染）、
      字段映射（`scripts/gen_field_mapping.py` → 269 条 / 34 表）均从 DDL 生成
      （[ADR-0005](../docs/adr/0005-ddl-as-contract-source-of-truth.md)）

## Phase 3 — 采集层

- [x] `ingestors/base.py`：Ingestor 协议。核心契约只含
      **证券标识 + 日线 OHLCV + 复权因子**；财报/指数/基金/期货/特色数据为可选能力
- [x] `ingestors/fuyao/`：**新写**客户端（未复用 `hfkit.py` —— 它属于另一个
      私有仓；凭据仍走仓外 `credentials.env` 的做法）
- [x] **新写**行情 + 复权因子 Ingestor。复权因子取 `adjust=none|forward|backward`
      三种价格之比，不重算除权除息数学
- [x] 第二个数据源的接入示例 → [`docs/adding-an-ingestor.md`](../docs/adding-an-ingestor.md)。
      不绑具体数据源，讲清怎么写自己的 Ingestor 与三条易踩的坑。
      抽象有效性由 `FakeIngestor` 实测（合成数据、无网络、无凭据），
      走完同一 writer 与 schema 后 `v_daily_qfq.close == raw.close * forward_factor`
      仍成立、覆盖写幂等 —— 换数据源时除 Ingestor 外无任何代码需改动

## Phase 4 — 文档

- [x] `docs/data-sources.md`：每个数据域的数据来源、上游接口、最小输入契约
- [x] **字段映射关系** → [`docs/field-mapping.md`](../docs/field-mapping.md)，
      与 data-sources.md 分开。前者 269 条机械映射由生成器产出，
      后者是人读的来源说明
- [x] **负面实验记录单独成章** → [`docs/negative-results.md`](../docs/negative-results.md)
      7 个被否决指标（MAVP / VP / SAREXT / KST / EFI / CG / RVGI）逐条记录了
      否决证据，并区分了「实测是坏的」与「当前 schema 装不下」两种否决原因；
      附教训「能算、不报错、值域离谱」与手工复算流程
- [x] 声明策略层私有（[ADR-0003](../docs/adr/0003-open-tooling-keep-strategies-private.md)）

## Phase 5 — 清理与 CI

- [x] **确认不迁入**：`strategies/`（11 文件）、`b1.md`、`scripts/b1_screen.sql`
      私有仓中的真实资金安排（单笔仓位、分批节奏的具体数字）比战法定义本身更敏感
- [x] `.bak.*` 剔除 —— 本仓从零 `git init`，未沿用任何历史，不存在此问题
- [x] 修正失真表述 —— `AGENTS.md` 属于私有仓未迁入；本仓文档中的
      "77 张表"（实为 62）与"零主键"（实为 59/62 有主键）已更正
- [x] CI 四道闸门（`scripts/ci_checks.py` + `.github/workflows/ci.yml`）：
      1. DDL 可执行性校验（逐域建干净库）
      2. 结构一致性（DDL vs 源库；无源库时跳过）
      3. 密钥扫描（硬编码凭据 / 高熵串 / UUID 放行）
      4. 开发者本机绝对路径泄漏扫描
- [x] shebang：新脚本统一 `#!/usr/bin/env python3`；迁入的指标脚本无 shebang，
      以 `python scripts/x.py` 调用

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
