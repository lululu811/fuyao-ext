# 字段字典

<!-- 本文件由 scripts/gen_field_dictionary.py 生成，请勿手工编辑。 -->

数据契约的字段字典，全部从 [`schema/*.sql`](../schema) 推导，无手工维护成分。
改 DDL 后重新运行生成器。

术语定义见 [`CONTEXT.md`](../CONTEXT.md)。

> **关于主键**：DuckDB 不强制主键约束，表中的「PK」标记表达的是
> 「这一组列应当唯一」的设计意图，不等于唯一性被数据库保证。
> 详见 [`schema/README.md`](../schema/README.md)。


## 行情（`market`）

9 张基表 / 4 个视图


### `_import_batches`

| 列 | 类型 | 说明 |
|---|---|---|
| `batch_id` **PK** | `VARCHAR` |  |
| `source` | `VARCHAR` |  |
| `kind` | `VARCHAR` |  |
| `started_at` | `TIMESTAMP` |  |
| `finished_at` | `TIMESTAMP` |  |
| `row_count` | `BIGINT` |  |
| `notes` | `VARCHAR` |  |

### `_meta`

| 列 | 类型 | 说明 |
|---|---|---|
| `key` **PK** | `VARCHAR` |  |
| `value` | `VARCHAR` |  |
| `updated_at` | `TIMESTAMP` |  |

### `calc_adjust_factor_daily`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `date` **PK** | `DATE` | 交易日 |
| `forward_factor` | `DOUBLE` | 前复权因子；`close * forward_factor` = 前复权收盘价 |
| `backward_factor` | `DOUBLE` | 后复权因子；`close * backward_factor` = 后复权收盘价 |
| `factor_version` | `VARCHAR` |  |
| `source_event_batch_id` | `VARCHAR` |  |
| `calculated_at` | `TIMESTAMP` |  |

### `dim_symbol`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `exchange` | `VARCHAR` |  |
| `asset_type` | `VARCHAR` |  |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |
| `updated_at` | `TIMESTAMP` |  |

### `raw_adjustment_events`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `ex_date` **PK** | `DATE` |  |
| `dividend_per_share` | `DOUBLE` |  |
| `per_share_bonus` | `DOUBLE` |  |
| `allotment_ratio` | `DOUBLE` |  |
| `allotment_price` | `DOUBLE` |  |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |

### `raw_kline_daily`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `date` **PK** | `DATE` | 交易日 |
| `open` | `DOUBLE` | 开盘价（未复权） |
| `high` | `DOUBLE` | 最高价（未复权） |
| `low` | `DOUBLE` | 最低价（未复权） |
| `close` | `DOUBLE` | 收盘价（未复权） |
| `volume` | `DOUBLE` | 成交量（股） |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `interval` | `VARCHAR` | K 线周期，本项目仅 `1d` |
| `adjusted` | `VARCHAR` | 价格口径；`raw_*` 表恒为 `none`（未复权） |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |

### `stg_adjustment_events`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `ex_date` | `DATE` |  |
| `dividend_per_share` | `DOUBLE` |  |
| `per_share_bonus` | `DOUBLE` |  |
| `allotment_ratio` | `DOUBLE` |  |
| `allotment_price` | `DOUBLE` |  |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |

### `stg_kline_daily`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `date` | `DATE` | 交易日 |
| `open` | `DOUBLE` | 开盘价（未复权） |
| `high` | `DOUBLE` | 最高价（未复权） |
| `low` | `DOUBLE` | 最低价（未复权） |
| `close` | `DOUBLE` | 收盘价（未复权） |
| `volume` | `DOUBLE` | 成交量（股） |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `interval` | `VARCHAR` | K 线周期，本项目仅 `1d` |
| `adjusted` | `VARCHAR` | 价格口径；`raw_*` 表恒为 `none`（未复权） |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |

### `stg_symbols`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `exchange` | `VARCHAR` |  |
| `asset_type` | `VARCHAR` |  |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |

视图（只读面，定义见 `schema/market.sql`）：

- `v_daily`
- `v_daily_hfq`
- `v_daily_qfq`
- `v_symbol`


## 财报（`financials`）

9 张基表 / 7 个视图


### `_import_batches`

| 列 | 类型 | 说明 |
|---|---|---|
| `batch_id` **PK** | `VARCHAR` |  |
| `source` | `VARCHAR` |  |
| `kind` | `VARCHAR` |  |
| `started_at` | `TIMESTAMP` |  |
| `finished_at` | `TIMESTAMP` |  |
| `row_count` | `BIGINT` |  |
| `notes` | `VARCHAR` |  |

### `_meta`

| 列 | 类型 | 说明 |
|---|---|---|
| `key` **PK** | `VARCHAR` |  |
| `value` | `VARCHAR` |  |
| `updated_at` | `TIMESTAMP` |  |

### `raw_balance_sheet`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `period` **PK** | `VARCHAR` |  |
| `period_end_ms` **PK** | `BIGINT` |  |
| `report_date_ms` | `BIGINT` |  |
| `fiscal_year` | `INTEGER` |  |
| `fiscal_period` | `VARCHAR` |  |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `total_current_assets` | `DOUBLE` |  |
| `non_current_nets_total` | `DOUBLE` |  |
| `assets_total` | `DOUBLE` |  |
| `total_debt` | `DOUBLE` |  |
| `holder_equity_total` | `DOUBLE` |  |
| `cash` | `DOUBLE` |  |
| `accounts_receivable` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_cash_flow_statement`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `period` **PK** | `VARCHAR` |  |
| `period_end_ms` **PK** | `BIGINT` |  |
| `report_date_ms` | `BIGINT` |  |
| `fiscal_year` | `INTEGER` |  |
| `fiscal_period` | `VARCHAR` |  |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `act_cash_flow_net` | `DOUBLE` |  |
| `invest_cash_flow_net` | `DOUBLE` |  |
| `financing_cash_flow_net` | `DOUBLE` |  |
| `cash_equivalents_net_addition` | `DOUBLE` |  |
| `pay_dividends_profits_interest_cash` | `DOUBLE` |  |
| `pay_fixed_assets_etc_cash` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_financial_indicators`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `report` **PK** | `VARCHAR` |  |
| `abilities_json` | `JSON` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_financial_indicators_detail`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `report` **PK** | `VARCHAR` |  |
| `operating_income_yoy` | `DOUBLE` |  |
| `operating_profit_yoy` | `DOUBLE` |  |
| `total_assets_growth_ratio` | `DOUBLE` |  |
| `fixed_asset_invest_expansion_ratio` | `DOUBLE` |  |
| `parent_holder_net_profit_yoy` | `DOUBLE` |  |
| `total_assets_net_ratio` | `DOUBLE` |  |
| `deduct_weighted_avg_roe` | `DOUBLE` |  |
| `sale_gross_margin` | `DOUBLE` |  |
| `sale_net_interest_ratio` | `DOUBLE` |  |
| `weighted_avg_roe` | `DOUBLE` |  |
| `current_ratio` | `DOUBLE` |  |
| `cash_ratio` | `DOUBLE` |  |
| `quick_ratio` | `DOUBLE` |  |
| `earned_interest_multiple` | `DOUBLE` |  |
| `assets_debt_ratio` | `DOUBLE` |  |
| `total_assets_turnover_ratio` | `DOUBLE` |  |
| `inventory_turnover_ratio` | `DOUBLE` |  |
| `long_term_debt_equity_ratio` | `DOUBLE` |  |
| `current_assets_turnover_ratio` | `DOUBLE` |  |
| `receive_account_turnover_ratio` | `DOUBLE` |  |
| `net_profit_cash_content` | `DOUBLE` |  |
| `cash_operating_index` | `DOUBLE` |  |
| `operating_cash_flow_net_divide_income` | `DOUBLE` |  |
| `cash_meet_invest_ratio` | `DOUBLE` |  |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_income_statement`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `period` **PK** | `VARCHAR` |  |
| `period_end_ms` **PK** | `BIGINT` |  |
| `report_date_ms` | `BIGINT` |  |
| `fiscal_year` | `INTEGER` |  |
| `fiscal_period` | `VARCHAR` |  |
| `currency` | `VARCHAR` | 币种；A 股恒为 CNY |
| `basic_eps` | `DOUBLE` |  |
| `operating_income` | `DOUBLE` |  |
| `operating_costs` | `DOUBLE` |  |
| `operating_expenses` | `DOUBLE` |  |
| `operating_profit` | `DOUBLE` |  |
| `profit_total` | `DOUBLE` |  |
| `net_profit` | `DOUBLE` |  |
| `parent_holder_net_profit` | `DOUBLE` |  |
| `income_tax_expense` | `DOUBLE` |  |
| `interest_expenses` | `DOUBLE` |  |
| `manage_fee` | `DOUBLE` |  |
| `sales_fee` | `DOUBLE` |  |
| `research_and_development_expenses` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_trading_calendar`

| 列 | 类型 | 说明 |
|---|---|---|
| `trade_date` **PK** | `DATE` |  |
| `date_ms` | `BIGINT` |  |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_valuation_snapshot`

| 列 | 类型 | 说明 |
|---|---|---|
| `snapshot_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `pe_ttm` | `DOUBLE` |  |
| `pe_mrq` | `DOUBLE` |  |
| `pb_mrq` | `DOUBLE` |  |
| `ps_ttm` | `DOUBLE` |  |
| `pcf_ttm` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

视图（只读面，定义见 `schema/financials.sql`）：

- `v_balance_sheet`
- `v_cash_flow_statement`
- `v_financial_indicators`
- `v_financial_indicators_detail`
- `v_income_statement`
- `v_trading_calendar`
- `v_valuation_latest`


## 指数（`index`）

6 张基表 / 4 个视图


### `_import_batches`

| 列 | 类型 | 说明 |
|---|---|---|
| `batch_id` **PK** | `VARCHAR` |  |
| `source` | `VARCHAR` |  |
| `kind` | `VARCHAR` |  |
| `started_at` | `TIMESTAMP` |  |
| `finished_at` | `TIMESTAMP` |  |
| `row_count` | `BIGINT` |  |
| `notes` | `VARCHAR` |  |

### `_meta`

| 列 | 类型 | 说明 |
|---|---|---|
| `key` **PK** | `VARCHAR` |  |
| `value` | `VARCHAR` |  |
| `updated_at` | `TIMESTAMP` |  |

### `raw_index_constituents`

| 列 | 类型 | 说明 |
|---|---|---|
| `index_thscode` **PK** | `VARCHAR` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_index_daily`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `trade_date` **PK** | `DATE` |  |
| `date_ms` | `BIGINT` |  |
| `open` | `DOUBLE` | 开盘价（未复权） |
| `high` | `DOUBLE` | 最高价（未复权） |
| `low` | `DOUBLE` | 最低价（未复权） |
| `close` | `DOUBLE` | 收盘价（未复权） |
| `volume` | `DOUBLE` | 成交量（股） |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_index_snapshot`

| 列 | 类型 | 说明 |
|---|---|---|
| `snapshot_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `name` | `VARCHAR` |  |
| `last_price` | `DOUBLE` |  |
| `price_change` | `DOUBLE` |  |
| `price_change_ratio` | `DOUBLE` |  |
| `open` | `DOUBLE` | 开盘价（未复权） |
| `high` | `DOUBLE` | 最高价（未复权） |
| `low` | `DOUBLE` | 最低价（未复权） |
| `volume` | `DOUBLE` | 成交量（股） |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_index_universe`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `name` | `VARCHAR` |  |
| `tag` | `VARCHAR` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

视图（只读面，定义见 `schema/index.sql`）：

- `v_index_constituents`
- `v_index_daily`
- `v_index_latest`
- `v_index_universe`


## 基金（`fund`）

15 张基表 / 10 个视图


### `_import_batches`

| 列 | 类型 | 说明 |
|---|---|---|
| `batch_id` **PK** | `VARCHAR` |  |
| `source` | `VARCHAR` |  |
| `kind` | `VARCHAR` |  |
| `started_at` | `TIMESTAMP` |  |
| `finished_at` | `TIMESTAMP` |  |
| `row_count` | `BIGINT` |  |
| `notes` | `VARCHAR` |  |

### `_meta`

| 列 | 类型 | 说明 |
|---|---|---|
| `key` **PK** | `VARCHAR` |  |
| `value` | `VARCHAR` |  |
| `updated_at` | `TIMESTAMP` |  |

### `raw_etf_daily`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `trade_date` **PK** | `DATE` |  |
| `open` | `DOUBLE` | 开盘价（未复权） |
| `high` | `DOUBLE` | 最高价（未复权） |
| `low` | `DOUBLE` | 最低价（未复权） |
| `close` | `DOUBLE` | 收盘价（未复权） |
| `volume` | `DOUBLE` | 成交量（股） |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |

### `raw_etf_snapshot`

| 列 | 类型 | 说明 |
|---|---|---|
| `trade_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `last_price` | `DOUBLE` |  |
| `open` | `DOUBLE` | 开盘价（未复权） |
| `high` | `DOUBLE` | 最高价（未复权） |
| `low` | `DOUBLE` | 最低价（未复权） |
| `prev_price` | `DOUBLE` |  |
| `price_change` | `DOUBLE` |  |
| `price_change_ratio_pct` | `DOUBLE` |  |
| `price_amplitude_ratio_pct` | `DOUBLE` |  |
| `volume` | `DOUBLE` | 成交量（股） |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `turnover_ratio_pct` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_etf_universe`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `exchange` | `VARCHAR` |  |
| `asset_type` | `VARCHAR` |  |
| `list_date` | `DATE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |
| `estab_date_ms` | `BIGINT` |  |

### `raw_fund_company`

| 列 | 类型 | 说明 |
|---|---|---|
| `company_id` **PK** | `VARCHAR` |  |
| `company_name` | `VARCHAR` |  |
| `company_type` | `VARCHAR` |  |
| `established_date_ms` | `BIGINT` |  |
| `fund_count` | `INTEGER` |  |
| `scale` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_fund_drawdowns`

| 列 | 类型 | 说明 |
|---|---|---|
| `fund_thscode` **PK** | `VARCHAR` |  |
| `dd_week` | `DOUBLE` |  |
| `dd_month` | `DOUBLE` |  |
| `dd_tmonth` | `DOUBLE` |  |
| `dd_hyear` | `DOUBLE` |  |
| `dd_year` | `DOUBLE` |  |
| `dd_twoyear` | `DOUBLE` |  |
| `dd_tyear` | `DOUBLE` |  |
| `dd_fyear` | `DOUBLE` |  |
| `dd_nowyear` | `DOUBLE` |  |
| `dd_now` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_fund_holders`

| 列 | 类型 | 说明 |
|---|---|---|
| `fund_thscode` **PK** | `VARCHAR` |  |
| `merge_scope` **PK** | `VARCHAR` |  |
| `report_date_ms` **PK** | `BIGINT` |  |
| `ins_position` | `DOUBLE` |  |
| `holder_amount` | `INTEGER` |  |
| `avg_holder_share` | `DOUBLE` |  |
| `psnl_rate` | `DOUBLE` |  |
| `mgmt_staff_hold_rate` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_fund_nav`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `nav_date` **PK** | `DATE` |  |
| `unit_nav` | `DOUBLE` |  |
| `adj_nav` | `DOUBLE` |  |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |
| `unit_nav_usable` | `BOOLEAN` |  |

### `raw_fund_news`

| 列 | 类型 | 说明 |
|---|---|---|
| `article_id` **PK** | `VARCHAR` |  |
| `title` | `VARCHAR` |  |
| `fund_thscode` | `VARCHAR` |  |
| `publish_date_ms` | `BIGINT` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_fund_offerings`

| 列 | 类型 | 说明 |
|---|---|---|
| `fund_thscode` **PK** | `VARCHAR` |  |
| `fund_name` | `VARCHAR` |  |
| `offering_start_ms` **PK** | `BIGINT` |  |
| `offering_end_ms` | `BIGINT` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_fund_portfolio_holdings`

| 列 | 类型 | 说明 |
|---|---|---|
| `fund_thscode` **PK** | `VARCHAR` |  |
| `stock_thscode` **PK** | `VARCHAR` |  |
| `stock_name` | `VARCHAR` |  |
| `hold_ratio` | `DOUBLE` |  |
| `position_count` | `DOUBLE` |  |
| `security_market_value_rate_pct` | `DOUBLE` |  |
| `period_increase_rate_pct` | `DOUBLE` |  |
| `investment_rank` | `INTEGER` |  |
| `start_date_ms` | `BIGINT` |  |
| `end_date_ms` | `BIGINT` |  |
| `publish_date_ms` **PK** | `BIGINT` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_fund_profile`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `fund_name` | `VARCHAR` |  |
| `estab_date` | `DATE` |  |
| `company_id` | `VARCHAR` |  |
| `mgmt_name` | `VARCHAR` |  |
| `manager_name` | `VARCHAR` |  |
| `fund_scale` | `DOUBLE` |  |
| `unit_nav` | `DOUBLE` |  |
| `manager_info` | `JSON` |  |
| `trade_rule` | `JSON` |  |
| `rate_info` | `JSON` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_fund_returns`

| 列 | 类型 | 说明 |
|---|---|---|
| `fund_thscode` **PK** | `VARCHAR` |  |
| `return_week` | `DOUBLE` |  |
| `return_month` | `DOUBLE` |  |
| `return_tmonth` | `DOUBLE` |  |
| `return_hyear` | `DOUBLE` |  |
| `return_year` | `DOUBLE` |  |
| `return_twoyear` | `DOUBLE` |  |
| `return_tyear` | `DOUBLE` |  |
| `return_fyear` | `DOUBLE` |  |
| `return_nowyear` | `DOUBLE` |  |
| `return_now` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_fund_top_holders`

| 列 | 类型 | 说明 |
|---|---|---|
| `fund_thscode` **PK** | `VARCHAR` |  |
| `holder_name` **PK** | `VARCHAR` |  |
| `holder_type` | `VARCHAR` |  |
| `holder_code` | `VARCHAR` |  |
| `rank` | `INTEGER` |  |
| `hold_share` | `DOUBLE` |  |
| `hold_rate_pct` | `DOUBLE` |  |
| `report_date_ms` **PK** | `BIGINT` |  |
| `publish_date_ms` | `BIGINT` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

视图（只读面，定义见 `schema/fund.sql`）：

- `v_etf_daily`
- `v_etf_latest`
- `v_etf_universe`
- `v_fund_company`
- `v_fund_holders`
- `v_fund_holdings`
- `v_fund_nav`
- `v_fund_profile`
- `v_fund_returns`
- `v_fund_top_holders`


## 期货（`futures`）

9 张基表 / 5 个视图


### `_import_batches`

| 列 | 类型 | 说明 |
|---|---|---|
| `batch_id` **PK** | `VARCHAR` |  |
| `source` | `VARCHAR` |  |
| `kind` | `VARCHAR` |  |
| `started_at` | `TIMESTAMP` |  |
| `finished_at` | `TIMESTAMP` |  |
| `row_count` | `BIGINT` |  |
| `notes` | `VARCHAR` |  |

### `_meta`

| 列 | 类型 | 说明 |
|---|---|---|
| `key` **PK** | `VARCHAR` |  |
| `value` | `VARCHAR` |  |
| `updated_at` | `TIMESTAMP` |  |

### `raw_futures_basis`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `trade_date` **PK** | `DATE` |  |
| `spot_price` | `DOUBLE` |  |
| `converted_spot_price` | `DOUBLE` |  |
| `close_price` | `DOUBLE` |  |
| `settle_price` | `DOUBLE` |  |
| `close_basis` | `DOUBLE` |  |
| `settle_basis` | `DOUBLE` |  |
| `close_basis_rate` | `DOUBLE` |  |
| `settle_basis_rate` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_futures_contracts`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `variety_code` | `VARCHAR` |  |
| `variety_name` | `VARCHAR` |  |
| `exchange_code` | `VARCHAR` |  |
| `list_date` | `DATE` |  |
| `end_date` | `DATE` |  |
| `last_trade_date` | `DATE` |  |
| `last_delivery_date` | `DATE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_futures_daily`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `trade_date` **PK** | `DATE` |  |
| `open_price` | `DOUBLE` |  |
| `high_price` | `DOUBLE` |  |
| `low_price` | `DOUBLE` |  |
| `close_price` | `DOUBLE` |  |
| `volume` | `DOUBLE` | 成交量（股） |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |

### `raw_futures_intraday`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `trade_date` **PK** | `DATE` |  |
| `session` **PK** | `VARCHAR` |  |
| `bar_ts` **PK** | `BIGINT` |  |
| `price` | `DOUBLE` |  |
| `volume` | `DOUBLE` | 成交量（股） |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `source_batch_id` | `VARCHAR` | 溯源：写入该行的批次号，见 `_import_batches` |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_futures_positions_variety`

| 列 | 类型 | 说明 |
|---|---|---|
| `trade_date` **PK** | `DATE` |  |
| `variety_code` **PK** | `VARCHAR` |  |
| `exchange_code` | `VARCHAR` |  |
| `open_interest` | `DOUBLE` |  |
| `open_interest_change` | `DOUBLE` |  |
| `volume` | `DOUBLE` | 成交量（股） |
| `long_open_interest` | `DOUBLE` |  |
| `short_open_interest` | `DOUBLE` |  |
| `long_short_ratio` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_futures_varieties`

| 列 | 类型 | 说明 |
|---|---|---|
| `variety_code` **PK** | `VARCHAR` |  |
| `exchange_code` **PK** | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `quote_code` | `VARCHAR` |  |
| `has_night_session` | `BOOLEAN` |  |
| `margin_rate` | `DOUBLE` |  |
| `main_contract_thscode` | `VARCHAR` |  |
| `trade_amount` | `VARCHAR` |  |
| `price_coefficient` | `DOUBLE` |  |
| `price_unit` | `VARCHAR` |  |
| `trade_unit` | `VARCHAR` |  |
| `tick_size` | `DOUBLE` |  |
| `contract_multiplier` | `DOUBLE` |  |
| `capital_flow` | `VARCHAR` |  |
| `long_short_ratio` | `VARCHAR` |  |
| `transaction_fee` | `VARCHAR` |  |
| `transaction_fee_rate` | `VARCHAR` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_futures_warehouse_receipts`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `trade_date` **PK** | `DATE` |  |
| `amount` | `DOUBLE` |  |
| `amount_change` | `DOUBLE` |  |
| `equivalent_lots` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

视图（只读面，定义见 `schema/futures.sql`）：

- `v_futures_contracts`
- `v_futures_daily`
- `v_futures_intraday`
- `v_futures_latest`
- `v_futures_varieties`


## 特色数据（`special`）

13 张基表 / 11 个视图


### `_import_batches`

| 列 | 类型 | 说明 |
|---|---|---|
| `batch_id` **PK** | `VARCHAR` |  |
| `source` | `VARCHAR` |  |
| `kind` | `VARCHAR` |  |
| `started_at` | `TIMESTAMP` |  |
| `finished_at` | `TIMESTAMP` |  |
| `row_count` | `BIGINT` |  |
| `notes` | `VARCHAR` |  |

### `_meta`

| 列 | 类型 | 说明 |
|---|---|---|
| `key` **PK** | `VARCHAR` |  |
| `value` | `VARCHAR` |  |
| `updated_at` | `TIMESTAMP` |  |

### `raw_anomaly_list`

| 列 | 类型 | 说明 |
|---|---|---|
| `capture_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `stock_name` | `VARCHAR` |  |
| `tag_name` **PK** | `VARCHAR` |  |
| `analysis_content` | `VARCHAR` |  |
| `keyword_list` | `JSON` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_auction_benchmark`

| 列 | 类型 | 说明 |
|---|---|---|
| `benchmark_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `auction_pct` | `DOUBLE` |  |
| `tags` | `VARCHAR` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_auction_snapshot`

| 列 | 类型 | 说明 |
|---|---|---|
| `snapshot_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `auction_price` | `DOUBLE` |  |
| `auction_pct` | `DOUBLE` |  |
| `auction_volume` | `DOUBLE` |  |
| `auction_amount` | `DOUBLE` |  |
| `auction_unmatched` | `DOUBLE` |  |
| `auction_turnover_pct` | `DOUBLE` |  |
| `auction_yesterday_ratio_pct` | `DOUBLE` |  |
| `auction_volume_ratio` | `DOUBLE` |  |
| `pre_close_price` | `DOUBLE` |  |
| `open_price` | `DOUBLE` |  |
| `last_price` | `DOUBLE` |  |
| `float_market_cap` | `DOUBLE` |  |
| `stage` **PK** | `VARCHAR` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_dragon_tiger`

| 列 | 类型 | 说明 |
|---|---|---|
| `trade_date` **PK** | `DATE` |  |
| `board_type` **PK** | `VARCHAR` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `name` | `VARCHAR` |  |
| `net_value` | `DOUBLE` |  |
| `net_rate` | `DOUBLE` |  |
| `buy_value` | `DOUBLE` |  |
| `sell_value` | `DOUBLE` |  |
| `org_net_value` | `DOUBLE` |  |
| `change` | `DOUBLE` |  |
| `hot_rank` | `INTEGER` |  |
| `range_days` | `INTEGER` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_hot_stock_history`

| 列 | 类型 | 说明 |
|---|---|---|
| `history_date` **PK** | `DATE` |  |
| `rank` | `INTEGER` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_hot_stock_list`

| 列 | 类型 | 说明 |
|---|---|---|
| `capture_date` **PK** | `DATE` |  |
| `period` **PK** | `VARCHAR` |  |
| `rank` | `INTEGER` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `heat` | `DOUBLE` |  |
| `rank_change` | `INTEGER` |  |
| `rank_trend` | `VARCHAR` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_hot_stock_rank_trend`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `trend_date` **PK** | `DATE` |  |
| `date_ms` | `BIGINT` |  |
| `rank` | `INTEGER` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_limit_break_pool`

| 列 | 类型 | 说明 |
|---|---|---|
| `trade_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `name` | `VARCHAR` |  |
| `last_price` | `DOUBLE` |  |
| `open_times` | `INTEGER` |  |
| `price_change_ratio` | `DOUBLE` |  |
| `turnover` | `DOUBLE` | 成交额（原始货币） |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_limit_down_pool`

| 列 | 类型 | 说明 |
|---|---|---|
| `trade_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `name` | `VARCHAR` |  |
| `last_price` | `DOUBLE` |  |
| `price_change_ratio` | `DOUBLE` |  |
| `first_limit_time` | `VARCHAR` |  |
| `last_limit_time` | `VARCHAR` |  |
| `turnover_ratio` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_limit_up_pool`

| 列 | 类型 | 说明 |
|---|---|---|
| `trade_date` **PK** | `DATE` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `name` | `VARCHAR` |  |
| `last_price` | `DOUBLE` |  |
| `continue_day_cnt` | `INTEGER` |  |
| `limit_up_time` | `VARCHAR` |  |
| `seal_money` | `DOUBLE` |  |
| `turnover_ratio` | `DOUBLE` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

### `raw_skyrocket_list`

| 列 | 类型 | 说明 |
|---|---|---|
| `capture_date` **PK** | `DATE` |  |
| `period` **PK** | `VARCHAR` |  |
| `rank` | `INTEGER` |  |
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `ticker` | `VARCHAR` |  |
| `name` | `VARCHAR` |  |
| `heat` | `DOUBLE` |  |
| `rank_change` | `INTEGER` |  |
| `rank_trend` | `VARCHAR` |  |
| `raw_payload` | `JSON` | 上游响应的原样留存（JSON） |
| `captured_at` | `TIMESTAMP` | 落库时刻 |

视图（只读面，定义见 `schema/special.sql`）：

- `v_anomaly_list`
- `v_auction_benchmark`
- `v_auction_snapshot`
- `v_dragon_tiger`
- `v_hot_stock`
- `v_hot_stock_history`
- `v_hot_stock_rank_trend`
- `v_limit_break_pool`
- `v_limit_down_pool`
- `v_limit_up_pool`
- `v_skyrocket`


## 指标（`indicators`）

1 张基表 / 0 个视图


### `v_indicators_daily`

| 列 | 类型 | 说明 |
|---|---|---|
| `thscode` **PK** | `VARCHAR` | 同花顺证券标识符，跨数据域通用主键 |
| `date` **PK** | `DATE` | 交易日 |
| `backend` | `VARCHAR` |  |
| `computed_at` | `TIMESTAMP` |  |
| `overlap_sma_5` | `DOUBLE` |  |
| `overlap_sma_10` | `DOUBLE` |  |
| `overlap_sma_20` | `DOUBLE` |  |
| `overlap_sma_60` | `DOUBLE` |  |
| `overlap_sma_120` | `DOUBLE` |  |
| `overlap_sma_250` | `DOUBLE` |  |
| `overlap_ema_5` | `DOUBLE` |  |
| `overlap_ema_10` | `DOUBLE` |  |
| `overlap_ema_20` | `DOUBLE` |  |
| `overlap_ema_60` | `DOUBLE` |  |
| `overlap_wma_20` | `DOUBLE` |  |
| `overlap_dema_20` | `DOUBLE` |  |
| `overlap_tema_20` | `DOUBLE` |  |
| `overlap_trima_20` | `DOUBLE` |  |
| `overlap_kama_14` | `DOUBLE` |  |
| `overlap_t3_5` | `DOUBLE` |  |
| `overlap_mama_mama` | `DOUBLE` |  |
| `overlap_mama_fama` | `DOUBLE` |  |
| `overlap_ht_trendline` | `DOUBLE` |  |
| `overlap_vwma_20` | `DOUBLE` |  |
| `overlap_hma_20` | `DOUBLE` |  |
| `overlap_alma_14` | `DOUBLE` |  |
| `overlap_vidya_14` | `DOUBLE` |  |
| `overlap_rma_14` | `DOUBLE` |  |
| `overlap_zlma_14` | `DOUBLE` |  |
| `overlap_mcgd_10` | `DOUBLE` |  |
| `overlap_fwma_20` | `DOUBLE` |  |
| `overlap_hwma_10` | `DOUBLE` |  |
| `overlap_jma_14` | `DOUBLE` |  |
| `overlap_pwma_14` | `DOUBLE` |  |
| `overlap_swma_10` | `DOUBLE` |  |
| `overlap_ssf_10` | `DOUBLE` |  |
| `overlap_sinwma_14` | `DOUBLE` |  |
| `momentum_rsi_6` | `DOUBLE` |  |
| `momentum_rsi_12` | `DOUBLE` |  |
| `momentum_rsi_14` | `DOUBLE` |  |
| `momentum_rsi_24` | `DOUBLE` |  |
| `momentum_macd_12_26_9_macd` | `DOUBLE` |  |
| `momentum_macd_12_26_9_signal` | `DOUBLE` |  |
| `momentum_macd_12_26_9_hist` | `DOUBLE` |  |
| `momentum_macd_5_35_5_macd` | `DOUBLE` |  |
| `momentum_macd_5_35_5_signal` | `DOUBLE` |  |
| `momentum_macd_5_35_5_hist` | `DOUBLE` |  |
| `momentum_stoch_14_3_3_slowk` | `DOUBLE` |  |
| `momentum_stoch_14_3_3_slowd` | `DOUBLE` |  |
| `momentum_stochrsi_14_fastk` | `DOUBLE` |  |
| `momentum_stochrsi_14_fastd` | `DOUBLE` |  |
| `momentum_willr_14` | `DOUBLE` |  |
| `momentum_cci_20` | `DOUBLE` |  |
| `momentum_adx_14` | `DOUBLE` |  |
| `momentum_aroon_25_aroonup` | `DOUBLE` |  |
| `momentum_aroon_25_aroondown` | `DOUBLE` |  |
| `momentum_kdj_9_3_k` | `DOUBLE` |  |
| `momentum_kdj_9_3_d` | `DOUBLE` |  |
| `momentum_kdj_9_3_j` | `DOUBLE` |  |
| `momentum_mom_10` | `DOUBLE` |  |
| `momentum_roc_10` | `DOUBLE` |  |
| `momentum_rocp_10` | `DOUBLE` |  |
| `momentum_rocr_10` | `DOUBLE` |  |
| `momentum_trix_15` | `DOUBLE` |  |
| `momentum_tsi_13_25` | `DOUBLE` |  |
| `momentum_cmo_14` | `DOUBLE` |  |
| `momentum_apo_12_26` | `DOUBLE` |  |
| `momentum_ppo_12_26` | `DOUBLE` |  |
| `momentum_stochf_5_3_fastk` | `DOUBLE` |  |
| `momentum_stochf_5_3_fastd` | `DOUBLE` |  |
| `momentum_er_10` | `DOUBLE` |  |
| `momentum_eri_13_bullp` | `DOUBLE` |  |
| `momentum_eri_13_bearp` | `DOUBLE` |  |
| `momentum_fisher_9_1_fisher` | `DOUBLE` |  |
| `momentum_fisher_9_1_signal` | `DOUBLE` |  |
| `momentum_qqe_14_5_qqe` | `DOUBLE` |  |
| `momentum_qqe_14_5_rsima` | `DOUBLE` |  |
| `momentum_qqe_14_5_long` | `DOUBLE` |  |
| `momentum_qqe_14_5_short` | `DOUBLE` |  |
| `momentum_qqe_14_5_band_long` | `DOUBLE` |  |
| `momentum_qqe_14_5_band_short` | `DOUBLE` |  |
| `momentum_qqe_14_5_diff` | `DOUBLE` |  |
| `momentum_rsx_14` | `DOUBLE` |  |
| `momentum_smi_5_20_5_smi` | `DOUBLE` |  |
| `momentum_smi_5_20_5_signal` | `DOUBLE` |  |
| `momentum_smi_5_20_5_oscillator` | `DOUBLE` |  |
| `momentum_dm_14_plus` | `DOUBLE` |  |
| `momentum_dm_14_minus` | `DOUBLE` |  |
| `momentum_brar_ar` | `DOUBLE` |  |
| `momentum_brar_br` | `DOUBLE` |  |
| `momentum_stc_line` | `DOUBLE` |  |
| `momentum_stc_macd` | `DOUBLE` |  |
| `momentum_stc_stoch` | `DOUBLE` |  |
| `momentum_lrsi_14` | `DOUBLE` |  |
| `momentum_bias_14` | `DOUBLE` |  |
| `momentum_ultosc_7_14_28` | `DOUBLE` |  |
| `momentum_ao_5_34` | `DOUBLE` |  |
| `momentum_coppock_10_10_14` | `DOUBLE` |  |
| `momentum_rvi_10_252` | `DOUBLE` |  |
| `trend_psar` | `DOUBLE` |  |
| `trend_adx_14` | `DOUBLE` |  |
| `trend_aroon_25_aroonup` | `DOUBLE` |  |
| `trend_aroon_25_aroondown` | `DOUBLE` |  |
| `trend_dpo_14` | `DOUBLE` |  |
| `trend_vortex_14_plus` | `DOUBLE` |  |
| `trend_vortex_14_minus` | `DOUBLE` |  |
| `trend_supertrend_10_3_0_trend` | `DOUBLE` |  |
| `trend_supertrend_10_3_0_direction` | `DOUBLE` |  |
| `trend_supertrend_10_3_0_long` | `DOUBLE` |  |
| `trend_supertrend_10_3_0_short` | `DOUBLE` |  |
| `trend_chop_14` | `DOUBLE` |  |
| `trend_inertia_20` | `DOUBLE` |  |
| `trend_decay_10` | `DOUBLE` |  |
| `trend_qstick_14` | `DOUBLE` |  |
| `trend_accbands_20_lower` | `DOUBLE` |  |
| `trend_accbands_20_mid` | `DOUBLE` |  |
| `trend_accbands_20_upper` | `DOUBLE` |  |
| `trend_vwmacd_12_26_9_macd` | `DOUBLE` |  |
| `trend_vwmacd_12_26_9_hist` | `DOUBLE` |  |
| `trend_vwmacd_12_26_9_signal` | `DOUBLE` |  |
| `trend_ichimoku_tenkan` | `DOUBLE` |  |
| `trend_ichimoku_kijun` | `DOUBLE` |  |
| `trend_ichimoku_senkou_a` | `DOUBLE` |  |
| `trend_ichimoku_senkou_b` | `DOUBLE` |  |
| `trend_ichimoku_chikou` | `DOUBLE` |  |
| `volatility_bbands_20_2_0_upper` | `DOUBLE` |  |
| `volatility_bbands_20_2_0_middle` | `DOUBLE` |  |
| `volatility_bbands_20_2_0_lower` | `DOUBLE` |  |
| `volatility_bbands_10_1_5_upper` | `DOUBLE` |  |
| `volatility_bbands_10_1_5_middle` | `DOUBLE` |  |
| `volatility_bbands_10_1_5_lower` | `DOUBLE` |  |
| `volatility_atr_14` | `DOUBLE` |  |
| `volatility_natr_14` | `DOUBLE` |  |
| `volatility_donchian_20_upper` | `DOUBLE` |  |
| `volatility_donchian_20_middle` | `DOUBLE` |  |
| `volatility_donchian_20_lower` | `DOUBLE` |  |
| `volatility_kc_20_2_lower` | `DOUBLE` |  |
| `volatility_kc_20_2_middle` | `DOUBLE` |  |
| `volatility_kc_20_2_upper` | `DOUBLE` |  |
| `volatility_trange` | `DOUBLE` |  |
| `volatility_vhf_14` | `DOUBLE` |  |
| `volume_obv` | `DOUBLE` |  |
| `volume_vosc_5_10` | `DOUBLE` |  |
| `volume_ha_open` | `DOUBLE` |  |
| `volume_ha_high` | `DOUBLE` |  |
| `volume_ha_low` | `DOUBLE` |  |
| `volume_ha_close` | `DOUBLE` |  |
| `volume_ad` | `DOUBLE` |  |
| `volume_adosc_3_10` | `DOUBLE` |  |
| `volume_mfi_14` | `DOUBLE` |  |
| `volume_cmf_20` | `DOUBLE` |  |
| `volume_vwap` | `DOUBLE` |  |
| `volume_pvt` | `DOUBLE` |  |
| `volume_nvi` | `DOUBLE` |  |
| `volume_pvi` | `DOUBLE` |  |
| `volume_emv` | `DOUBLE` |  |
| `volume_eom_14` | `DOUBLE` |  |
| `volume_kvo_34_55_kvo` | `DOUBLE` |  |
| `volume_kvo_34_55_signal` | `DOUBLE` |  |
| `volume_aobv_5_12_obv` | `DOUBLE` |  |
| `volume_aobv_5_12_min` | `DOUBLE` |  |
| `volume_aobv_5_12_max` | `DOUBLE` |  |
| `volume_aobv_5_12_ema5` | `DOUBLE` |  |
| `volume_aobv_5_12_ema12` | `DOUBLE` |  |
| `volume_aobv_5_12_lr` | `DOUBLE` |  |
| `volume_aobv_5_12_sr` | `DOUBLE` |  |
| `volume_vfi_13_0_5` | `DOUBLE` |  |
| `volume_wad` | `DOUBLE` |  |
| `volume_pvr` | `DOUBLE` |  |
| `cycles_ht_dcperiod` | `DOUBLE` |  |
| `cycles_ht_dcphase` | `DOUBLE` |  |
| `cycles_ht_phasor_inphase` | `DOUBLE` |  |
| `cycles_ht_phasor_quadrature` | `DOUBLE` |  |
| `cycles_ht_sine_sine` | `DOUBLE` |  |
| `cycles_ht_sine_leadsine` | `DOUBLE` |  |
| `cycles_ht_trendmode` | `DOUBLE` |  |
| `statistics_beta_20` | `DOUBLE` |  |
| `statistics_correl_20` | `DOUBLE` |  |
| `statistics_linearreg_14` | `DOUBLE` |  |
| `statistics_linearreg_angle_14` | `DOUBLE` |  |
| `statistics_linearreg_intercept_14` | `DOUBLE` |  |
| `statistics_linearreg_slope_14` | `DOUBLE` |  |
| `statistics_tsf_14` | `DOUBLE` |  |
| `statistics_stddev_20` | `DOUBLE` |  |
| `statistics_var_20` | `DOUBLE` |  |
| `statistics_entropy_10` | `DOUBLE` |  |
| `statistics_skew_30` | `DOUBLE` |  |
| `statistics_kurtosis_30` | `DOUBLE` |  |
| `statistics_zscore_20` | `DOUBLE` |  |
| `statistics_mad_20` | `DOUBLE` |  |
| `statistics_quantile_20_0_5` | `DOUBLE` |  |
| `statistics_ui_14` | `DOUBLE` |  |
| `performance_log_return_1` | `DOUBLE` |  |
| `performance_percent_return_1` | `DOUBLE` |  |
| `performance_drawdown_20_dd` | `DOUBLE` |  |
| `performance_drawdown_20_frac` | `DOUBLE` |  |
| `performance_drawdown_20_log` | `DOUBLE` |  |
| `zettaranc_zg_white_10` | `DOUBLE` |  |
| `zettaranc_dg_yellow_14` | `DOUBLE` |  |
| `zettaranc_bbi` | `DOUBLE` |  |
| `zettaranc_brick_value` | `DOUBLE` |  |
| `candles_cdl_2crows_0` | `DOUBLE` |  |
| `candles_cdl_3blackcrows_0` | `DOUBLE` |  |
| `candles_cdl_3inside_0` | `DOUBLE` |  |
| `candles_cdl_3linestrike_0` | `DOUBLE` |  |
| `candles_cdl_3outside_0` | `DOUBLE` |  |
| `candles_cdl_3starsinsouth_0` | `DOUBLE` |  |
| `candles_cdl_3whitesoldiers_0` | `DOUBLE` |  |
| `candles_cdl_abandonedbaby_0` | `DOUBLE` |  |
| `candles_cdl_advanceblock_0` | `DOUBLE` |  |
| `candles_cdl_belthold_0` | `DOUBLE` |  |
| `candles_cdl_breakaway_0` | `DOUBLE` |  |
| `candles_cdl_closingmarubozu_0` | `DOUBLE` |  |
| `candles_cdl_concealbabyswall_0` | `DOUBLE` |  |
| `candles_cdl_counterattack_0` | `DOUBLE` |  |
| `candles_cdl_darkcloudcover_0` | `DOUBLE` |  |
| `candles_cdl_doji_0` | `DOUBLE` |  |
| `candles_cdl_dojistar_0` | `DOUBLE` |  |
| `candles_cdl_dragonflydoji_0` | `DOUBLE` |  |
| `candles_cdl_engulfing_0` | `DOUBLE` |  |
| `candles_cdl_eveningdojistar_0` | `DOUBLE` |  |
| `candles_cdl_eveningstar_0` | `DOUBLE` |  |
| `candles_cdl_gapsidesidewhite_0` | `DOUBLE` |  |
| `candles_cdl_gravestonedoji_0` | `DOUBLE` |  |
| `candles_cdl_hammer_0` | `DOUBLE` |  |
| `candles_cdl_hangingman_0` | `DOUBLE` |  |
| `candles_cdl_harami_0` | `DOUBLE` |  |
| `candles_cdl_haramicross_0` | `DOUBLE` |  |
| `candles_cdl_highwave_0` | `DOUBLE` |  |
| `candles_cdl_hikkake_0` | `DOUBLE` |  |
| `candles_cdl_hikkakemod_0` | `DOUBLE` |  |
| `candles_cdl_homingpigeon_0` | `DOUBLE` |  |
| `candles_cdl_identical3crows_0` | `DOUBLE` |  |
| `candles_cdl_inneck_0` | `DOUBLE` |  |
| `candles_cdl_invertedhammer_0` | `DOUBLE` |  |
| `candles_cdl_kicking_0` | `DOUBLE` |  |
| `candles_cdl_kickingbylength_0` | `DOUBLE` |  |
| `candles_cdl_ladderbottom_0` | `DOUBLE` |  |
| `candles_cdl_longleggeddoji_0` | `DOUBLE` |  |
| `candles_cdl_longline_0` | `DOUBLE` |  |
| `candles_cdl_marubozu_0` | `DOUBLE` |  |
| `candles_cdl_matchinglow_0` | `DOUBLE` |  |
| `candles_cdl_mathold_0` | `DOUBLE` |  |
| `candles_cdl_morningdojistar_0` | `DOUBLE` |  |
| `candles_cdl_morningstar_0` | `DOUBLE` |  |
| `candles_cdl_onneck_0` | `DOUBLE` |  |
| `candles_cdl_piercing_0` | `DOUBLE` |  |
| `candles_cdl_rickshawman_0` | `DOUBLE` |  |
| `candles_cdl_risefall3methods_0` | `DOUBLE` |  |
| `candles_cdl_separatinglines_0` | `DOUBLE` |  |
| `candles_cdl_shootingstar_0` | `DOUBLE` |  |
| `candles_cdl_shortline_0` | `DOUBLE` |  |
| `candles_cdl_spinningtop_0` | `DOUBLE` |  |
| `candles_cdl_stalledpattern_0` | `DOUBLE` |  |
| `candles_cdl_sticksandwich_0` | `DOUBLE` |  |
| `candles_cdl_takuri_0` | `DOUBLE` |  |
| `candles_cdl_tasukigap_0` | `DOUBLE` |  |
| `candles_cdl_thrusting_0` | `DOUBLE` |  |
| `candles_cdl_tristar_0` | `DOUBLE` |  |
| `candles_cdl_unique3river_0` | `DOUBLE` |  |
| `candles_cdl_upsidegap2crows_0` | `DOUBLE` |  |
| `candles_cdl_xsidegap3methods_0` | `DOUBLE` |  |

---
共 **62** 张基表、**846** 个基表列。

