# 字段映射：上游字段 -> 数据契约列

<!-- 本文件由 scripts/gen_field_mapping.py 生成，请勿手工编辑。 -->

本文件是自建 Ingestor 的直接依据：给定一个数据源，按这里的映射把它的字段
落到契约列上即可。目标列的定义以 [`schema/*.sql`](../schema) 为准。

**「转换」列的记法**

| 记法 | 含义 |
|---|---|
| `直接取` | 上游同名字段，直接取值 |
| `常量` | 固定值，与数据源无关 |
| `表达式` | 需要转换，见备注 |
| `需人工确认` | 静态解析不出来，**请自行判断**，不要照抄 |

> 标为「需人工确认」的条目占少数。这些多半是跨表派生或复杂计算，
> 不同数据源的处理方式可能不同，抄错会静默产出错误数据。


共抽取 **269** 条映射，覆盖 **34** 张表（其中 12 条需人工确认）。


## `raw_anomaly_list`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `analysis_content` | 直接取 `analysis_content`（来自 `item`） | — |
| `capture_date` | 变量 `today` | — |
| `keyword_list` | 经 `dumps()` 转换 | — |
| `stock_name` | 直接取 `stock_name`（来自 `item`） | — |
| `tag_name` | 变量 `tag` | — |
| `thscode` | 变量 `code` | — |

## `raw_auction_benchmark`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `auction_pct` | 直接取 `auction_pct`（来自 `item`） | — |
| `benchmark_date` | 变量 `date_str` | — |
| `name` | 直接取 `name`（来自 `item`） | — |
| `tags` | 变量 `tags_str` | — |
| `thscode` | 变量 `code` | — |
| `ticker` | 直接取 `ticker`（来自 `item`） | — |

## `raw_dragon_tiger`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `board_type` | 变量 `board_type` | — |
| `buy_value` | 直接取 `buy_value`（来自 `r`） | — |
| `change` | 直接取 `change`（来自 `r`） | — |
| `hot_rank` | 直接取 `hot_rank`（来自 `r`） | — |
| `name` | 直接取 `name`（来自 `r`） | — |
| `net_rate` | 直接取 `net_rate`（来自 `r`） | — |
| `net_value` | 直接取 `net_value`（来自 `r`） | — |
| `org_net_value` | 直接取 `org_net_value`（来自 `r`） | — |
| `range_days` | 直接取 `range_days`（来自 `r`） | — |
| `sell_value` | 直接取 `sell_value`（来自 `r`） | — |
| `thscode` | 变量 `code` | — |
| `trade_date` | 变量 `date_str` | — |

## `raw_etf_daily`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `close` | 需人工确认 | r.get('close_price') or r.get('close') |
| `high` | 需人工确认 | r.get('high_price') or r.get('high') |
| `low` | 需人工确认 | r.get('low_price') or r.get('low') |
| `open` | 需人工确认 | r.get('open_price') or r.get('open') |
| `thscode` | 变量 `code` | — |
| `trade_date` | 变量 `dt` | — |
| `turnover` | 直接取 `turnover`（来自 `r`） | — |
| `volume` | 直接取 `volume`（来自 `r`） | — |

## `raw_etf_snapshot`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `high` | 直接取 `high_price`（来自 `s`） | — |
| `last_price` | 直接取 `last_price`（来自 `s`） | — |
| `low` | 直接取 `low_price`（来自 `s`） | — |
| `name` | 直接取 `name`（来自 `s`） | — |
| `open` | 直接取 `open_price`（来自 `s`） | — |
| `prev_price` | 直接取 `prev_price`（来自 `s`） | — |
| `price_amplitude_ratio_pct` | 直接取 `price_amplitude_ratio_pct`（来自 `s`） | — |
| `price_change` | 直接取 `price_change`（来自 `s`） | — |
| `price_change_ratio_pct` | 直接取 `price_change_ratio_pct`（来自 `s`） | — |
| `thscode` | 变量 `code` | — |
| `ticker` | 直接取 `ticker`（来自 `s`） | — |
| `trade_date` | 经属性 `date` | — |
| `turnover` | 直接取 `turnover`（来自 `s`） | — |
| `turnover_ratio_pct` | 直接取 `turnover_ratio_pct`（来自 `s`） | — |
| `volume` | 直接取 `volume`（来自 `s`） | — |

## `raw_etf_universe`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `asset_type` | 变量 `asset_type` | — |
| `exchange` | 直接取 `exchange`（来自 `r`） | — |
| `list_date` | 直接取 `list_date`（来自 `r`） | — |
| `name` | 直接取 `name`（来自 `r`） | — |
| `thscode` | 变量 `code` | — |
| `ticker` | 直接取 `ticker`（来自 `r`） | — |

## `raw_financial_indicators`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `abilities_json` | 经 `dumps()` 转换 | — |
| `report` | 变量 `report` | — |
| `thscode` | 变量 `thscode` | — |

## `raw_financial_indicators_detail`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `report` | 变量 `report` | — |
| `thscode` | 变量 `thscode` | — |

## `raw_fund_company`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `company_id` | 变量 `cid` | — |
| `company_name` | 直接取 `company_name`（来自 `item`） | — |
| `company_type` | 直接取 `company_type`（来自 `item`） | — |
| `established_date_ms` | 直接取 `established_date_ms`（来自 `item`） | — |
| `fund_count` | 直接取 `fund_count`（来自 `item`） | — |
| `scale` | 直接取 `scale`（来自 `item`） | — |

## `raw_fund_drawdowns`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `dd_fyear` | 直接取 `fyear`（来自 `item`） | — |
| `dd_hyear` | 直接取 `hyear`（来自 `item`） | — |
| `dd_month` | 直接取 `month`（来自 `item`） | — |
| `dd_now` | 直接取 `now`（来自 `item`） | — |
| `dd_nowyear` | 直接取 `nowyear`（来自 `item`） | — |
| `dd_tmonth` | 直接取 `tmonth`（来自 `item`） | — |
| `dd_twoyear` | 直接取 `twoyear`（来自 `item`） | — |
| `dd_tyear` | 直接取 `tyear`（来自 `item`） | — |
| `dd_week` | 直接取 `week`（来自 `item`） | — |
| `dd_year` | 直接取 `year`（来自 `item`） | — |
| `fund_thscode` | 变量 `fund` | — |

## `raw_fund_holders`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `avg_holder_share` | 直接取 `avg_holder_share`（来自 `item`） | — |
| `fund_thscode` | 变量 `fund` | — |
| `holder_amount` | 直接取 `holder_amount`（来自 `item`） | — |
| `ins_position` | 直接取 `ins_position`（来自 `item`） | — |
| `merge_scope` | 变量 `scope` | — |
| `mgmt_staff_hold_rate` | 直接取 `mgmt_staff_hold_rate`（来自 `item`） | — |
| `psnl_rate` | 直接取 `psnl_rate`（来自 `item`） | — |
| `report_date_ms` | 变量 `ms` | — |

## `raw_fund_nav`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `adj_nav` | 变量 `adj` | — |
| `nav_date` | 变量 `nav_date` | — |
| `thscode` | 变量 `code` | — |
| `unit_nav` | 变量 `unit` | — |
| `unit_nav_usable` | 变量 `usable` | — |

## `raw_fund_news`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `article_id` | 变量 `aid` | — |
| `fund_thscode` | 直接取 `thscode`（来自 `item`） | — |
| `publish_date_ms` | 直接取 `publish_date_ms`（来自 `item`） | — |
| `title` | 直接取 `title`（来自 `item`） | — |

## `raw_fund_offerings`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `fund_name` | 直接取 `fund_name`（来自 `item`） | — |
| `fund_thscode` | 变量 `fund` | — |
| `offering_end_ms` | 直接取 `offering_end_ms`（来自 `item`） | — |
| `offering_start_ms` | 变量 `ms` | — |

## `raw_fund_portfolio_holdings`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `end_date_ms` | 直接取 `end_date_ms`（来自 `item`） | — |
| `fund_thscode` | 变量 `fund` | — |
| `hold_ratio` | 直接取 `hold_ratio`（来自 `item`） | — |
| `investment_rank` | 直接取 `investment_rank`（来自 `item`） | — |
| `period_increase_rate_pct` | 直接取 `period_increase_rate_pct`（来自 `item`） | — |
| `position_count` | 直接取 `position_count`（来自 `item`） | — |
| `publish_date_ms` | 变量 `pub_ms` | — |
| `security_market_value_rate_pct` | 直接取 `security_market_value_rate_pct`（来自 `item`） | — |
| `start_date_ms` | 直接取 `start_date_ms`（来自 `item`） | — |
| `stock_name` | 直接取 `stock_name`（来自 `item`） | — |
| `stock_thscode` | 变量 `stock` | — |

## `raw_fund_profile`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `company_id` | 直接取 `company_id`（来自 `p`） | — |
| `estab_date` | 经 `ms_to_date()` 转换 | — |
| `fund_name` | 直接取 `fund_name`（来自 `p`） | — |
| `fund_scale` | 直接取 `fund_scale`（来自 `p`） | — |
| `manager_info` | 经 `dumps()` 转换 | — |
| `manager_name` | 直接取 `manager_name`（来自 `p`） | — |
| `mgmt_name` | 直接取 `mgmt_name`（来自 `p`） | — |
| `rate_info` | 经 `dumps()` 转换 | — |
| `thscode` | 变量 `code` | — |
| `ticker` | 直接取 `ticker`（来自 `p`） | — |
| `trade_rule` | 经 `dumps()` 转换 | — |
| `unit_nav` | 直接取 `unit_nav`（来自 `p`） | — |

## `raw_fund_returns`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `fund_thscode` | 变量 `fund` | — |
| `return_fyear` | 直接取 `return_fyear`（来自 `item`） | — |
| `return_hyear` | 直接取 `return_hyear`（来自 `item`） | — |
| `return_month` | 直接取 `return_month`（来自 `item`） | — |
| `return_now` | 直接取 `return_now`（来自 `item`） | — |
| `return_nowyear` | 直接取 `return_nowyear`（来自 `item`） | — |
| `return_tmonth` | 直接取 `return_tmonth`（来自 `item`） | — |
| `return_twoyear` | 直接取 `return_twoyear`（来自 `item`） | — |
| `return_tyear` | 直接取 `return_tyear`（来自 `item`） | — |
| `return_week` | 直接取 `return_week`（来自 `item`） | — |
| `return_year` | 直接取 `return_year`（来自 `item`） | — |

## `raw_fund_top_holders`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `fund_thscode` | 变量 `fund` | — |
| `hold_rate_pct` | 直接取 `hold_rate_pct`（来自 `item`） | — |
| `hold_share` | 直接取 `hold_share`（来自 `item`） | — |
| `holder_code` | 直接取 `holder_code`（来自 `item`） | — |
| `holder_name` | 变量 `name` | — |
| `holder_type` | 直接取 `holder_type`（来自 `item`） | — |
| `publish_date_ms` | 直接取 `publish_date_ms`（来自 `item`） | — |
| `rank` | 直接取 `rank`（来自 `item`） | — |
| `report_date_ms` | 变量 `ms` | — |

## `raw_futures_basis`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `close_basis` | 直接取 `close_basis`（来自 `r`） | — |
| `close_basis_rate` | 直接取 `close_basis_rate`（来自 `r`） | — |
| `close_price` | 直接取 `close_price`（来自 `r`） | — |
| `converted_spot_price` | 直接取 `converted_spot_price`（来自 `r`） | — |
| `settle_basis` | 直接取 `settle_basis`（来自 `r`） | — |
| `settle_basis_rate` | 直接取 `settle_basis_rate`（来自 `r`） | — |
| `settle_price` | 直接取 `settle_price`（来自 `r`） | — |
| `spot_price` | 直接取 `spot_price`（来自 `r`） | — |
| `thscode` | 经属性 `thscode` | — |
| `trade_date` | 变量 `dt` | — |

## `raw_futures_contracts`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `end_date` | 直接取 `end_date`（来自 `c`） | — |
| `exchange_code` | 直接取 `exchange_code`（来自 `c`） | — |
| `last_delivery_date` | 直接取 `last_delivery_date`（来自 `c`） | — |
| `last_trade_date` | 直接取 `last_trade_date`（来自 `c`） | — |
| `list_date` | 直接取 `list_date`（来自 `c`） | — |
| `name` | 直接取 `name`（来自 `c`） | — |
| `thscode` | 变量 `thscode` | — |
| `ticker` | 直接取 `ticker`（来自 `c`） | — |
| `variety_code` | 直接取 `variety_code`（来自 `c`） | — |
| `variety_name` | 直接取 `variety_name`（来自 `c`） | — |

## `raw_futures_daily`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `close_price` | 直接取 `close_price`（来自 `r`） | — |
| `high_price` | 直接取 `high_price`（来自 `r`） | — |
| `low_price` | 直接取 `low_price`（来自 `r`） | — |
| `open_price` | 直接取 `open_price`（来自 `r`） | — |
| `thscode` | 变量 `code` | — |
| `trade_date` | 变量 `dt` | — |
| `turnover` | 直接取 `turnover`（来自 `r`） | — |
| `volume` | 直接取 `volume`（来自 `r`） | — |

## `raw_futures_intraday`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `bar_ts` | 变量 `bar_ts` | — |
| `price` | 直接取 `price`（来自 `r`） | — |
| `session` | 经属性 `session` | — |
| `thscode` | 变量 `code` | — |
| `trade_date` | 经属性 `date` | — |
| `turnover` | 直接取 `turnover`（来自 `r`） | — |
| `volume` | 直接取 `volume`（来自 `r`） | — |

## `raw_futures_positions_variety`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `exchange_code` | 直接取 `exchange_code`（来自 `r`） | — |
| `long_open_interest` | 直接取 `long_open_interest`（来自 `r`） | — |
| `long_short_ratio` | 直接取 `long_short_ratio`（来自 `r`） | — |
| `open_interest` | 直接取 `open_interest`（来自 `r`） | — |
| `open_interest_change` | 直接取 `open_interest_change`（来自 `r`） | — |
| `short_open_interest` | 直接取 `short_open_interest`（来自 `r`） | — |
| `trade_date` | 经属性 `date` | — |
| `variety_code` | 变量 `vc` | — |
| `volume` | 直接取 `volume`（来自 `r`） | — |

## `raw_futures_varieties`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `capital_flow` | 直接取 `capital_flow`（来自 `r`） | — |
| `contract_multiplier` | 直接取 `contract_multiplier`（来自 `r`） | — |
| `exchange_code` | 变量 `ex` | — |
| `has_night_session` | 经 `bool()` 转换 | — |
| `long_short_ratio` | 直接取 `long_short_ratio`（来自 `r`） | — |
| `main_contract_thscode` | 直接取 `main_contract_thscode`（来自 `r`） | — |
| `margin_rate` | 直接取 `margin_rate`（来自 `r`） | — |
| `name` | 直接取 `name`（来自 `r`） | — |
| `price_coefficient` | 直接取 `price_coefficient`（来自 `r`） | — |
| `price_unit` | 直接取 `price_unit`（来自 `r`） | — |
| `quote_code` | 直接取 `quote_code`（来自 `r`） | — |
| `tick_size` | 直接取 `tick_size`（来自 `r`） | — |
| `trade_amount` | 直接取 `trade_amount`（来自 `r`） | — |
| `trade_unit` | 直接取 `trade_unit`（来自 `r`） | — |
| `transaction_fee` | 直接取 `transaction_fee`（来自 `r`） | — |
| `transaction_fee_rate` | 直接取 `transaction_fee_rate`（来自 `r`） | — |
| `variety_code` | 变量 `vc` | — |

## `raw_futures_warehouse_receipts`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `amount` | 直接取 `amount`（来自 `r`） | — |
| `amount_change` | 直接取 `amount_change`（来自 `r`） | — |
| `equivalent_lots` | 直接取 `equivalent_lots`（来自 `r`） | — |
| `thscode` | 经属性 `thscode` | — |
| `trade_date` | 变量 `dt` | — |

## `raw_hot_stock_history`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `history_date` | 变量 `date_str` | — |
| `name` | 直接取 `name`（来自 `item`） | — |
| `rank` | 直接取 `rank`（来自 `item`） | — |
| `thscode` | 变量 `code` | — |
| `ticker` | 直接取 `ticker`（来自 `item`） | — |

## `raw_index_constituents`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `index_thscode` | 变量 `index_code` | — |
| `name` | 直接取 `name`（来自 `item`） | — |
| `thscode` | 变量 `stock_code` | — |
| `ticker` | 直接取 `ticker`（来自 `item`） | — |

## `raw_index_daily`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `close` | 直接取 `close_price`（来自 `r`） | — |
| `date_ms` | 变量 `dms` | — |
| `high` | 直接取 `high_price`（来自 `r`） | — |
| `low` | 直接取 `low_price`（来自 `r`） | — |
| `open` | 直接取 `open_price`（来自 `r`） | — |
| `thscode` | 变量 `thscode` | — |
| `trade_date` | 经 `ms_to_date()` 转换 | — |
| `turnover` | 直接取 `turnover`（来自 `r`） | — |
| `volume` | 直接取 `volume`（来自 `r`） | — |

## `raw_index_snapshot`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `high` | 需人工确认 | item.get('high_price') or item.get('high') |
| `last_price` | 直接取 `last_price`（来自 `item`） | — |
| `low` | 需人工确认 | item.get('low_price') or item.get('low') |
| `name` | 直接取 `name`（来自 `item`） | — |
| `open` | 需人工确认 | item.get('open_price') or item.get('open') |
| `price_change` | 直接取 `price_change`（来自 `item`） | — |
| `price_change_ratio` | 需人工确认 | item.get('price_change_ratio_pct') or item.get('price_change_ratio') |
| `snapshot_date` | 变量 `today` | — |
| `thscode` | 变量 `code` | — |
| `turnover` | 直接取 `turnover`（来自 `item`） | — |
| `volume` | 直接取 `volume`（来自 `item`） | — |

## `raw_index_universe`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `name` | 直接取 `name`（来自 `item`） | — |
| `tag` | 变量 `tag` | — |
| `thscode` | 变量 `code` | — |

## `raw_limit_break_pool`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `last_price` | 直接取 `last_price`（来自 `r`） | — |
| `name` | 直接取 `name`（来自 `r`） | — |
| `open_times` | 直接取 `open_times`（来自 `r`） | — |
| `price_change_ratio` | 需人工确认 | r.get('price_change_ratio_pct') or r.get('price_change_ratio') |
| `thscode` | 变量 `code` | — |
| `trade_date` | 变量 `date_str` | — |
| `turnover` | 直接取 `turnover`（来自 `r`） | — |

## `raw_limit_down_pool`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `first_limit_time` | 直接取 `first_limit_time`（来自 `r`） | — |
| `last_limit_time` | 直接取 `last_limit_time`（来自 `r`） | — |
| `last_price` | 直接取 `last_price`（来自 `r`） | — |
| `name` | 直接取 `name`（来自 `r`） | — |
| `price_change_ratio` | 需人工确认 | r.get('price_change_ratio_pct') or r.get('price_change_ratio') |
| `thscode` | 变量 `code` | — |
| `trade_date` | 变量 `date_str` | — |
| `turnover_ratio` | 需人工确认 | r.get('turnover_ratio_pct') or r.get('turnover_ratio') |

## `raw_limit_up_pool`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `continue_day_cnt` | 直接取 `continue_day_cnt`（来自 `r`） | — |
| `last_price` | 直接取 `last_price`（来自 `r`） | — |
| `limit_up_time` | 直接取 `limit_up_time`（来自 `r`） | — |
| `name` | 直接取 `name`（来自 `r`） | — |
| `seal_money` | 直接取 `seal_money`（来自 `r`） | — |
| `thscode` | 变量 `code` | — |
| `trade_date` | 变量 `date_str` | — |
| `turnover_ratio` | 需人工确认 | r.get('turnover_ratio_pct') or r.get('turnover_ratio') |

## `raw_valuation_snapshot`

| 契约列 | 上游来源 | 转换 |
|---|---|---|
| `name` | 直接取 `name`（来自 `item`） | — |
| `pb_mrq` | 直接取 `pb_mrq`（来自 `item`） | — |
| `pcf_ttm` | 直接取 `pcf_ttm`（来自 `item`） | — |
| `pe_mrq` | 直接取 `pe_mrq`（来自 `item`） | — |
| `pe_ttm` | 直接取 `pe_ttm`（来自 `item`） | — |
| `ps_ttm` | 直接取 `ps_ttm`（来自 `item`） | — |
| `snapshot_date` | 变量 `today` | — |
| `thscode` | 变量 `code` | — |
| `ticker` | 直接取 `ticker`（来自 `item`） | — |
