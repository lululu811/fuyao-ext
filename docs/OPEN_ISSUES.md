# 公开前必须处理的问题

> 本文件记录**已确认存在、但需要你拍板才能改**的问题。
> 与 [`OPEN_SOURCE_PLAN.md`](OPEN_SOURCE_PLAN.md) 的区别：那是执行步骤，这是待决策清单。
>
> **当前状态：3 项已解决，0 项待决。**

---

## 1. ✅ RSL 双重实现 — 已解决

### 曾经的判断（错误）

此前记录称 config 路径与脚本路径"产出不同值"。**经核实为误判。**

`calc_rsl_short/long` 用 `rolling(length*5, min_periods=length)`，
`add_zettaranc_columns.py` 用固定 `rolling(15, min_periods=3)` / `rolling(105, min_periods=21)`。
`length*5` 在 length=3 和 21 时恰好得到 15 和 105，`min_periods` 也一致 ——
**两条路径数值完全等价**。

### 真实问题与解决

与线上表逐列比对后，实际情况是：

| 路径 | 列名 | 是否存在于线上表 |
|---|---|---|
| `indicators_config.yaml` 的 `zettaranc:` 类目 | `zettaranc_rsl_short_3`<br>`zettaranc_rsl_long_21` | ❌ **从未被应用** |
| `scripts/add_zettaranc_columns.py` | `zettaranc_rsl_rank_15`<br>`zettaranc_rsl_rank_105` | ✅ 实际存在 |

config 里的两条是**从未生效的孤儿配置**。任何人运行一次 `add_indicators.py` 的
config 差集回填，就会往 21.6 GB 的宽表里多灌两列与现有列数值等价的重复 RSL。

**已从 `indicators_config.yaml` 移除这两条。** 对线上表零影响（这两列本就不存在），
并消除了未来回填出重复列的风险。

现在 config 推导 262 列，是线上表 264 列的真子集；
多出的 2 列由 `add_zettaranc_columns.py` 正确地独立管辖。

### 遗留的架构不一致（不阻塞发布）

`zettaranc` 类目中其余 4 个指标（`zg_white` / `dg_yellow` / `bbi` / `brick_value`）
**同时**被 config 和 `add_zettaranc_columns.py` 两条路径计算，只因前四者恰好同名
（`zettaranc_zg_white_10` 等）才没产生重复列 —— config 路径产出这些列，
脚本 `upsert` 时按主键覆盖，值等价因而无害。

若要彻底消除双实现，需要给 `calc_rsl` 引入二级参数（回看周期 ≠ 排名窗口），
因为 config 的列名由单一 `params` 推导
（`indicator/compute.py:50-53`）。**这是接口改动，不值得为开源而做。**
现状已在 config 中就地注释说明。

---

## 2. ✅ zettaranc 6 列的数据可用性 — 已核实可用

`add_zettaranc_columns.py` 的历史注释曾记录：因 import 顺序错误导致该脚本每次运行
都 `ModuleNotFoundError` 崩溃，**6 列从未被真正计算过**；库中那批 0 值是
`add_indicators.py` 写的。

**该问题早已修复，只是注释未更新。** 对线上表实测（预热期后 9,897,247 行，
`date > 2017-06-01`）：

| 列 | 非空率 | 备注 |
|---|---|---|
| `zettaranc_zg_white_10` | 99.53% | |
| `zettaranc_dg_yellow_14` | 96.92% | 零值行数 **0** |
| `zettaranc_bbi` | 99.40% | |
| `zettaranc_brick_value` | 100.00% | |
| `zettaranc_rsl_rank_15` | 99.87% | 零值行数 **0**，均值 **53.41** |
| `zettaranc_rsl_rank_105` | 98.92% | |

`rsl_rank_15` 是 `[0,100]` 上的百分位排名，理论均值约 50，实测 53.41 ——
**数值正确，不是占位值。** 6 列均可正常用于下游策略。

已更新 `add_zettaranc_columns.py` 中的过时注释。

---

## 3. ✅ `schema/` 缺显式 `__init__.py` — 已修

上游 `a-stock/schema/` 目录下**没有 `__init__.py`**，靠 Python 3.3+ 的隐式
namespace package 才能 `import schema.indicators_schema`。

本仓库已新增 `schema/__init__.py`。
