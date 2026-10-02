# 数据契约

本目录下的 `.sql` 是**数据契约的可执行定义**。依据
[ADR-0005](../docs/adr/0005-ddl-as-contract-source-of-truth.md)，
它们是模型的唯一事实源；本目录之外的一切模型描述（表清单、字段字典、
ER 图）都由它们生成，不手工维护。

## 怎么用

```bash
# 建全套表（每个数据域一个独立的 DuckDB 文件，与上游的物理布局一致）
duckdb market.duckdb     < market.sql
duckdb financials.duckdb < financials.sql
duckdb index.duckdb      < index.sql
duckdb fund.duckdb       < fund.sql
duckdb futures.duckdb    < futures.sql
duckdb special.duckdb    < special.sql
duckdb indicators.duckdb < indicators.sql
```

⚠️ **不要把所有域建进同一个库。** `_meta` 与 `_import_batches` 在每个域中
都有定义，跨域重名，一次性 `cat *.sql` 会因重名失败。保持每域一个文件，
与上游的物理布局一致。`scripts/ci_checks.py` 也是逐域建库校验的。

**这里只有结构，没有数据。** 数据需自行获取并灌入 —— 见
[`data-sources.md`](../docs/data-sources.md)。

## 文件

| 文件 | 数据域 | 基表 | 视图 | DDL 来源 |
|---|---|---|---|---|
| `market.sql` | 行情 | 9 | 4 | 现存库 |
| `financials.sql` | 财报 | 9 | 7 | 现存库 |
| `index.sql` | 指数 | 6 | 4 | 现存库 |
| `fund.sql` | 基金 | 15 | 10 | 现存库 |
| `futures.sql` | 期货 | 9 | 5 | 现存库 |
| `special.sql` | 特色数据 | 13 | 11 | 现存库 |
| `indicators.sql` | 指标 | 1 | 0 | **`indicators_config.yaml` 推导** |
| | **合计** | **62** | **41** | |

`indicators.sql` 与其它文件来源不同：指标表是本项目自己的计算产物，
其结构由 `indicators_config.yaml` 推导（`schema/indicators_schema.py`），
不是从库中反射出来的。改列、���参数、改后端都改 config，然后重新导出。

## 四层结构

| 层 | 角色 | 本契约中的体现 |
|---|---|---|
| `raw_*` | 上游数据落地面，字段保持上游语义 | 有主键的完整落地表 |
| `stg_*` | 批量导入中转层 | **3 张，全部为空** |
| `dim_*` | 维度表 | `dim_symbol` |
| `v_*` | 读取面 | 41 个视图 |

**关于空的 `stg_*` 表**：`stg_kline_daily`、`stg_adjustment_events`、`stg_symbols`
是早期批量导入路径的残留，当前 0 行且**没有声明主键**（62 张表中仅这 3 张没有）。
它们保留在契约中是为了说明"曾经存在过一条 staging 路径"，
但**不是使用者必须实现的**——自建采集器时可直接写入 `raw_*`。

术语的精确定义见 [`CONTEXT.md`](../CONTEXT.md)。

## 主键

62 张表中 **59 张声明了 PRIMARY KEY**，未声明的 3 张正是上面那三张空的 `stg_*`。

⚠️ **DuckDB 不强制主键约束。** `PRIMARY KEY` 在 DuckDB 中只用于建立 ART 索引，
插入重复键不会报错。声明了主键**不等于**唯一性被保证。

因此本项目的契约把主键当作**声明性文档**：它表达"这一组列应当唯一"的设计意图，
实际唯一性需要使用者自行保证。`scripts/export_schema.py --check` 校验的是
**结构一致性**，不校验数据唯一性。

## 维护

```bash
python scripts/export_schema.py           # 重新导出
python scripts/export_schema.py --check   # 只校验，不写（CI 用）
```

导出器会：

1. 只读打开各源库，取 `duckdb_tables().sql` / `duckdb_views().sql`
2. 在内存探测库中建表并迭代建视图，得到视图的**拓扑序**
3. 把生成的 DDL 灌进干净的内存库，与现存库**逐对象逐列比对**
4. `--check` 模式下额外比对已提交的 `.sql` 与现存库是否同步

改动源库结构或 `indicators_config.yaml` 后，务必重新运行导出并提交。
