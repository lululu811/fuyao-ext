# 写一个自己的 Ingestor

本项目自带一个参考实现（[`ingestors/fuyao/`](../ingestors/fuyao)），
但**它不是必需的**。采集层的抽象只要求你能产出三样东西：

| 需要 | 目标表 | 说明 |
|---|---|---|
| 证券标识 | `dim_symbol` | `thscode` + `ticker` / `name` / `exchange` / `asset_type` / `currency` |
| 日线 OHLCV | `raw_kline_daily` | **未复权**原始价 |
| 复权因子 | `calc_adjust_factor_daily` | `forward_factor` / `backward_factor` |

财务、指数、基金、期货、特色数据属于**可选能力**，不做也能满足核心契约。

---

## 最短路径

实现四个方法即可。协议在 [`ingestors/base.py`](../ingestors/base.py)：

```python
import pandas as pd
from ingestors.base import IngestorInfo, validate


class MyIngestor:
    def describe(self) -> IngestorInfo:
        return IngestorInfo(
            name="我的数据源",
            homepage="https://example.com",
            credential_env="MY_API_KEY",
            credential_help="https://example.com/keys",
            notes="日线数据 T+1 更新；停牌日不补行",
        )

    def list_symbols(self) -> pd.DataFrame:
        rows = fetch_all_symbols()          # 你的取数逻辑
        return validate(pd.DataFrame(rows), "dim_symbol")

    def fetch_daily_bars(self, thscode: str, start: str, end: str) -> pd.DataFrame:
        rows = fetch_bars(thscode, start, end)
        df = pd.DataFrame(rows).rename(columns={"vol": "volume"})
        df["thscode"] = thscode
        df["interval"] = "1d"
        df["adjusted"] = "none"           # 必须是未复权
        df["currency"] = "CNY"
        return validate(df, "raw_kline_daily")

    def fetch_adjust_factors(self, thscode: str, start: str, end: str) -> pd.DataFrame:
        df = compute_factors(thscode, start, end)
        return validate(df, "calc_adjust_factor_daily")
```

**就这样。** writer、schema、下游的指标引擎全都不用改。

落库直接复用现成的 writer：

```python
from ingestors.fuyao.writer import DuckDbMarketWriter, new_batch_id

with DuckDbMarketWriter("market.duckdb") as w:
    w.init_schema()                                  # 按 schema/market.sql 建表
    bid = new_batch_id("market")
    w.write("raw_kline_daily", bars, batch_id=bid)
    w.write("calc_adjust_factor_daily", factors, batch_id=bid)
```

`source_batch_id`、`calculated_at` 这类溯源列由 writer 自动填，你不用管。

---

## 三条容易踩的

### 1. `raw_kline_daily` 必须是未复权价

这一列存原始价，复权**由因子表承担**。如果你在价格里预先复权了，
`v_daily_qfq` 视图就会二次复权，而且因子无从校验。

契约靠这个恒等式成立：

```
close * forward_factor == 前复权收盘价
```

`tests/test_ingestor_contract.py::test_adjustment_identity_holds_after_roundtrip`
会验证它。

### 2. 因子口径必须和你自己的价格一致

因子不是独立于行情的外部数据，它必须和 `raw_kline_daily` 出自同一口径。
校验方式：

```python
from ingestors.base import check_factor_consistency

report = check_factor_consistency(bars, factors)
if not report["ok"]:
    ...  # 因子没回填，或口径错乱
```

### 3. 证券标识要能映射

`thscode` 是跨数据域的通用主键。如果你的数据源用 6 位代码（如 `600519`）
而不是同花顺标识（`600519.SH`），**映射由 Ingestor 负责**，不在契约内。

最简单的做法是拼上交易所后缀：

```python
df["thscode"] = df["ticker"] + "." + df["exchange"]   # 600519 + SH -> 600519.SH
```

---

## 复权因子怎么算

有两条路，推荐第一条。

**路线 A —— 从「复权价 ÷ 未复权价」取比值（推荐）**

如果你的数据源能同时返回未复权价和前/后复权价，直接取比值：

```
forward_factor  = 前复权收盘价 / 未复权收盘价
backward_factor = 后复权收盘价 / 未复权收盘价
```

好处是**不可能对不上** —— 因子直接由价格推导，不存在公式实现偏差。
参考实现走的就是这条路。

**路线 B —— 自己实现除权除息**

只有在数据源**不提供**复权价时才需要。代价是：任何一处假设偏差
（前收盘价取法、配股送股处理、停牌跨越除权日）都会让因子与实际价格对不上，
而且这种错误是静默的。可参见
[负面实验记录](negative-results.md)里的 EFI 案例。

---

## 跑测试

写完 Ingestor 后，先确认它满足协议：

```python
from ingestors.base import Ingestor
assert isinstance(MyIngestor(), Ingestor)
```

更实际的做法是照着 [`tests/test_ingestor_contract.py`](../tests/test_ingestor_contract.py)
里的 `FakeIngestor` 改造成你自己的实现。`FakeIngestor` 完全合成、不联网、
不需要凭据，是最快的调试脚手架。

---

## 上游参考实现的特殊之处

若你只是换数据源，不需要关心这些；记录在此以备查阅。

- **复权因子走路线 A**：调用上游同接口的 `adjust=none|forward|backward`
  三种价格取比值，不重算除权除息数学
- **单次请求窗口 10 年**：上游限制，超出会返回 `code=1003`，
  实现按 10 年切片（`market.py` 的 `_windows`）
- **重试策略**：连接错误、HTTP 408/429/5xx 与非业务错误码重试；
  业务错误（1002/1003/400/401/403）立即抛出 —— 重试一个坏请求是纯浪费
