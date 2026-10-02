# ER 图

<!-- 本文件由 scripts/gen_er_diagram.py 生成，请勿手工编辑。 -->

数据契约的实体关系图，全部从 [`schema/*.sql`](../schema) 推导。

> **关于外键**：数据契约**不声明 `FOREIGN KEY`**。下图中的关系是按共享键
> 推断的约定，不是数据库强制的完整性约束 —— DuckDB 也不强制主键。
> 实线是显式定义的关系，虚线是共享 `thscode` / `(thscode, date)` 推断的。
>
> 需要真实的约束保证时，请在你自己实现的 writer 里加校验。


## 核心契约

指标引擎只依赖这三张表。任何能产出它们的 Ingestor 都能接入。

```mermaid
erDiagram
    dim_symbol {
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        VARCHAR exchange
        VARCHAR asset_type
        VARCHAR currency
        VARCHAR source_batch_id
        TIMESTAMP updated_at
    }
    raw_kline_daily {
        VARCHAR PK thscode
        DATE PK date
        DOUBLE open
        DOUBLE high
        DOUBLE low
        DOUBLE close
        DOUBLE volume
        DOUBLE turnover
        VARCHAR currency
        VARCHAR interval
        VARCHAR adjusted
        VARCHAR source_batch_id
    }
    calc_adjust_factor_daily {
        VARCHAR PK thscode
        DATE PK date
        DOUBLE forward_factor
        DOUBLE backward_factor
        VARCHAR factor_version
        VARCHAR source_event_batch_id
        TIMESTAMP calculated_at
    }
    dim_symbol ||--o{ raw_kline_daily : thscode
    raw_kline_daily ||--|| calc_adjust_factor_daily : "thscode, date"
```

核心恒等式（`v_daily_qfq` 的定义）：

```
close * forward_factor == 前复权收盘价
```


## 行情（`market`）

7 张表。

```mermaid
erDiagram
    calc_adjust_factor_daily {
        VARCHAR PK thscode
        DATE PK date
        DOUBLE forward_factor
        DOUBLE backward_factor
        VARCHAR factor_version
        VARCHAR source_event_batch_id
        TIMESTAMP calculated_at
    }
    dim_symbol {
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        VARCHAR exchange
        VARCHAR asset_type
        VARCHAR currency
        VARCHAR source_batch_id
        TIMESTAMP updated_at
    }
    raw_adjustment_events {
        VARCHAR PK thscode
        VARCHAR ticker
        DATE PK ex_date
        DOUBLE dividend_per_share
        DOUBLE per_share_bonus
        DOUBLE allotment_ratio
        DOUBLE allotment_price
        VARCHAR currency
        VARCHAR source_batch_id
    }
    raw_kline_daily {
        VARCHAR PK thscode
        DATE PK date
        DOUBLE open
        DOUBLE high
        DOUBLE low
        DOUBLE close
        DOUBLE volume
        DOUBLE turnover
        VARCHAR currency
        VARCHAR interval
        VARCHAR adjusted
        VARCHAR source_batch_id
    }
    stg_adjustment_events {
        VARCHAR thscode
        VARCHAR ticker
        DATE ex_date
        DOUBLE dividend_per_share
        DOUBLE per_share_bonus
        DOUBLE allotment_ratio
        DOUBLE allotment_price
        VARCHAR currency
        VARCHAR source_batch_id
    }
    stg_kline_daily {
        VARCHAR thscode
        DATE date
        DOUBLE open
        DOUBLE high
        DOUBLE low
        DOUBLE close
        DOUBLE volume
        DOUBLE turnover
        VARCHAR currency
        VARCHAR interval
        VARCHAR adjusted
        VARCHAR source_batch_id
    }
    stg_symbols {
        VARCHAR thscode
        VARCHAR ticker
        VARCHAR name
        VARCHAR exchange
        VARCHAR asset_type
        VARCHAR currency
        VARCHAR source_batch_id
    }
    dim_symbol ||--o{ raw_kline_daily : "thscode"
    raw_kline_daily ||--o{ calc_adjust_factor_daily : "thscode, date"
    dim_symbol ||--o{ raw_adjustment_events : "thscode"
```

## 财报（`financials`）

7 张表。

```mermaid
erDiagram
    raw_balance_sheet {
        VARCHAR PK thscode
        VARCHAR PK period
        BIGINT PK period_end_ms
        BIGINT report_date_ms
        INTEGER fiscal_year
        VARCHAR fiscal_period
        VARCHAR currency
        DOUBLE total_current_assets
        DOUBLE non_current_nets_total
        DOUBLE assets_total
        DOUBLE total_debt
        DOUBLE holder_equity_total
        DOUBLE cash
        DOUBLE accounts_receivable
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_cash_flow_statement {
        VARCHAR PK thscode
        VARCHAR PK period
        BIGINT PK period_end_ms
        BIGINT report_date_ms
        INTEGER fiscal_year
        VARCHAR fiscal_period
        VARCHAR currency
        DOUBLE act_cash_flow_net
        DOUBLE invest_cash_flow_net
        DOUBLE financing_cash_flow_net
        DOUBLE cash_equivalents_net_addition
        DOUBLE pay_dividends_profits_interest_cash
        DOUBLE pay_fixed_assets_etc_cash
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_financial_indicators {
        VARCHAR PK thscode
        VARCHAR PK report
        JSON abilities_json
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_financial_indicators_detail {
        VARCHAR PK thscode
        VARCHAR PK report
        DOUBLE operating_income_yoy
        DOUBLE operating_profit_yoy
        DOUBLE total_assets_growth_ratio
        DOUBLE fixed_asset_invest_expansion_ratio
        DOUBLE parent_holder_net_profit_yoy
        DOUBLE total_assets_net_ratio
        DOUBLE deduct_weighted_avg_roe
        DOUBLE sale_gross_margin
        DOUBLE sale_net_interest_ratio
        DOUBLE weighted_avg_roe
        DOUBLE current_ratio
        DOUBLE cash_ratio
        DOUBLE quick_ratio
        DOUBLE earned_interest_multiple
        DOUBLE assets_debt_ratio
        DOUBLE total_assets_turnover_ratio
        DOUBLE inventory_turnover_ratio
        DOUBLE long_term_debt_equity_ratio
        DOUBLE current_assets_turnover_ratio
        DOUBLE receive_account_turnover_ratio
        DOUBLE net_profit_cash_content
        DOUBLE cash_operating_index
        DOUBLE operating_cash_flow_net_divide_income
        DOUBLE cash_meet_invest_ratio
        TIMESTAMP captured_at
    }
    raw_income_statement {
        VARCHAR PK thscode
        VARCHAR PK period
        BIGINT PK period_end_ms
        BIGINT report_date_ms
        INTEGER fiscal_year
        VARCHAR fiscal_period
        VARCHAR currency
        DOUBLE basic_eps
        DOUBLE operating_income
        DOUBLE operating_costs
        DOUBLE operating_expenses
        DOUBLE operating_profit
        DOUBLE profit_total
        DOUBLE net_profit
        DOUBLE parent_holder_net_profit
        DOUBLE income_tax_expense
        DOUBLE interest_expenses
        DOUBLE manage_fee
        DOUBLE sales_fee
        DOUBLE research_and_development_expenses
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_trading_calendar {
        DATE PK trade_date
        BIGINT date_ms
        TIMESTAMP captured_at
    }
    raw_valuation_snapshot {
        DATE PK snapshot_date
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        DOUBLE pe_ttm
        DOUBLE pe_mrq
        DOUBLE pb_mrq
        DOUBLE ps_ttm
        DOUBLE pcf_ttm
        JSON raw_payload
        TIMESTAMP captured_at
    }
```

## 指数（`index`）

4 张表。

```mermaid
erDiagram
    raw_index_constituents {
        VARCHAR PK index_thscode
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        TIMESTAMP captured_at
    }
    raw_index_daily {
        VARCHAR PK thscode
        DATE PK trade_date
        BIGINT date_ms
        DOUBLE open
        DOUBLE high
        DOUBLE low
        DOUBLE close
        DOUBLE volume
        DOUBLE turnover
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_index_snapshot {
        DATE PK snapshot_date
        VARCHAR PK thscode
        VARCHAR name
        DOUBLE last_price
        DOUBLE price_change
        DOUBLE price_change_ratio
        DOUBLE open
        DOUBLE high
        DOUBLE low
        DOUBLE volume
        DOUBLE turnover
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_index_universe {
        VARCHAR PK thscode
        VARCHAR name
        VARCHAR tag
        JSON raw_payload
        TIMESTAMP captured_at
    }
```

## 基金（`fund`）

13 张表。

```mermaid
erDiagram
    raw_etf_daily {
        VARCHAR PK thscode
        DATE PK trade_date
        DOUBLE open
        DOUBLE high
        DOUBLE low
        DOUBLE close
        DOUBLE volume
        DOUBLE turnover
        VARCHAR source_batch_id
    }
    raw_etf_snapshot {
        DATE PK trade_date
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        DOUBLE last_price
        DOUBLE open
        DOUBLE high
        DOUBLE low
        DOUBLE prev_price
        DOUBLE price_change
        DOUBLE price_change_ratio_pct
        DOUBLE price_amplitude_ratio_pct
        DOUBLE volume
        DOUBLE turnover
        DOUBLE turnover_ratio_pct
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_etf_universe {
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        VARCHAR exchange
        VARCHAR asset_type
        DATE list_date
        JSON raw_payload
        TIMESTAMP captured_at
        BIGINT estab_date_ms
    }
    raw_fund_company {
        VARCHAR PK company_id
        VARCHAR company_name
        VARCHAR company_type
        BIGINT established_date_ms
        INTEGER fund_count
        DOUBLE scale
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_fund_drawdowns {
        VARCHAR PK fund_thscode
        DOUBLE dd_week
        DOUBLE dd_month
        DOUBLE dd_tmonth
        DOUBLE dd_hyear
        DOUBLE dd_year
        DOUBLE dd_twoyear
        DOUBLE dd_tyear
        DOUBLE dd_fyear
        DOUBLE dd_nowyear
        DOUBLE dd_now
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_fund_holders {
        VARCHAR PK fund_thscode
        VARCHAR PK merge_scope
        BIGINT PK report_date_ms
        DOUBLE ins_position
        INTEGER holder_amount
        DOUBLE avg_holder_share
        DOUBLE psnl_rate
        DOUBLE mgmt_staff_hold_rate
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_fund_nav {
        VARCHAR PK thscode
        DATE PK nav_date
        DOUBLE unit_nav
        DOUBLE adj_nav
        VARCHAR source_batch_id
        BOOLEAN unit_nav_usable
    }
    raw_fund_news {
        VARCHAR PK article_id
        VARCHAR title
        VARCHAR fund_thscode
        BIGINT publish_date_ms
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_fund_offerings {
        VARCHAR PK fund_thscode
        VARCHAR fund_name
        BIGINT PK offering_start_ms
        BIGINT offering_end_ms
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_fund_portfolio_holdings {
        VARCHAR PK fund_thscode
        VARCHAR PK stock_thscode
        VARCHAR stock_name
        DOUBLE hold_ratio
        DOUBLE position_count
        DOUBLE security_market_value_rate_pct
        DOUBLE period_increase_rate_pct
        INTEGER investment_rank
        BIGINT start_date_ms
        BIGINT end_date_ms
        BIGINT PK publish_date_ms
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_fund_profile {
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR fund_name
        DATE estab_date
        VARCHAR company_id
        VARCHAR mgmt_name
        VARCHAR manager_name
        DOUBLE fund_scale
        DOUBLE unit_nav
        JSON manager_info
        JSON trade_rule
        JSON rate_info
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_fund_returns {
        VARCHAR PK fund_thscode
        DOUBLE return_week
        DOUBLE return_month
        DOUBLE return_tmonth
        DOUBLE return_hyear
        DOUBLE return_year
        DOUBLE return_twoyear
        DOUBLE return_tyear
        DOUBLE return_fyear
        DOUBLE return_nowyear
        DOUBLE return_now
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_fund_top_holders {
        VARCHAR PK fund_thscode
        VARCHAR PK holder_name
        VARCHAR holder_type
        VARCHAR holder_code
        INTEGER rank
        DOUBLE hold_share
        DOUBLE hold_rate_pct
        BIGINT PK report_date_ms
        BIGINT publish_date_ms
        JSON raw_payload
        TIMESTAMP captured_at
    }
```

## 期货（`futures`）

7 张表。

```mermaid
erDiagram
    raw_futures_basis {
        VARCHAR PK thscode
        DATE PK trade_date
        DOUBLE spot_price
        DOUBLE converted_spot_price
        DOUBLE close_price
        DOUBLE settle_price
        DOUBLE close_basis
        DOUBLE settle_basis
        DOUBLE close_basis_rate
        DOUBLE settle_basis_rate
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_futures_contracts {
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        VARCHAR variety_code
        VARCHAR variety_name
        VARCHAR exchange_code
        DATE list_date
        DATE end_date
        DATE last_trade_date
        DATE last_delivery_date
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_futures_daily {
        VARCHAR PK thscode
        DATE PK trade_date
        DOUBLE open_price
        DOUBLE high_price
        DOUBLE low_price
        DOUBLE close_price
        DOUBLE volume
        DOUBLE turnover
        VARCHAR source_batch_id
    }
    raw_futures_intraday {
        VARCHAR PK thscode
        DATE PK trade_date
        VARCHAR PK session
        BIGINT PK bar_ts
        DOUBLE price
        DOUBLE volume
        DOUBLE turnover
        VARCHAR source_batch_id
        TIMESTAMP captured_at
    }
    raw_futures_positions_variety {
        DATE PK trade_date
        VARCHAR PK variety_code
        VARCHAR exchange_code
        DOUBLE open_interest
        DOUBLE open_interest_change
        DOUBLE volume
        DOUBLE long_open_interest
        DOUBLE short_open_interest
        DOUBLE long_short_ratio
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_futures_varieties {
        VARCHAR PK variety_code
        VARCHAR PK exchange_code
        VARCHAR name
        VARCHAR quote_code
        BOOLEAN has_night_session
        DOUBLE margin_rate
        VARCHAR main_contract_thscode
        VARCHAR trade_amount
        DOUBLE price_coefficient
        VARCHAR price_unit
        VARCHAR trade_unit
        DOUBLE tick_size
        DOUBLE contract_multiplier
        VARCHAR capital_flow
        VARCHAR long_short_ratio
        VARCHAR transaction_fee
        VARCHAR transaction_fee_rate
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_futures_warehouse_receipts {
        VARCHAR PK thscode
        DATE PK trade_date
        DOUBLE amount
        DOUBLE amount_change
        DOUBLE equivalent_lots
        JSON raw_payload
        TIMESTAMP captured_at
    }
```

## 特色数据（`special`）

11 张表。

```mermaid
erDiagram
    raw_anomaly_list {
        DATE PK capture_date
        VARCHAR PK thscode
        VARCHAR stock_name
        VARCHAR PK tag_name
        VARCHAR analysis_content
        JSON keyword_list
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_auction_benchmark {
        DATE PK benchmark_date
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        DOUBLE auction_pct
        VARCHAR tags
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_auction_snapshot {
        DATE PK snapshot_date
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        DOUBLE auction_price
        DOUBLE auction_pct
        DOUBLE auction_volume
        DOUBLE auction_amount
        DOUBLE auction_unmatched
        DOUBLE auction_turnover_pct
        DOUBLE auction_yesterday_ratio_pct
        DOUBLE auction_volume_ratio
        DOUBLE pre_close_price
        DOUBLE open_price
        DOUBLE last_price
        DOUBLE float_market_cap
        VARCHAR PK stage
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_dragon_tiger {
        DATE PK trade_date
        VARCHAR PK board_type
        VARCHAR PK thscode
        VARCHAR name
        DOUBLE net_value
        DOUBLE net_rate
        DOUBLE buy_value
        DOUBLE sell_value
        DOUBLE org_net_value
        DOUBLE change
        INTEGER hot_rank
        INTEGER range_days
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_hot_stock_history {
        DATE PK history_date
        INTEGER rank
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_hot_stock_list {
        DATE PK capture_date
        VARCHAR PK period
        INTEGER rank
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        DOUBLE heat
        INTEGER rank_change
        VARCHAR rank_trend
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_hot_stock_rank_trend {
        VARCHAR PK thscode
        DATE PK trend_date
        BIGINT date_ms
        INTEGER rank
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_limit_break_pool {
        DATE PK trade_date
        VARCHAR PK thscode
        VARCHAR name
        DOUBLE last_price
        INTEGER open_times
        DOUBLE price_change_ratio
        DOUBLE turnover
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_limit_down_pool {
        DATE PK trade_date
        VARCHAR PK thscode
        VARCHAR name
        DOUBLE last_price
        DOUBLE price_change_ratio
        VARCHAR first_limit_time
        VARCHAR last_limit_time
        DOUBLE turnover_ratio
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_limit_up_pool {
        DATE PK trade_date
        VARCHAR PK thscode
        VARCHAR name
        DOUBLE last_price
        INTEGER continue_day_cnt
        VARCHAR limit_up_time
        DOUBLE seal_money
        DOUBLE turnover_ratio
        JSON raw_payload
        TIMESTAMP captured_at
    }
    raw_skyrocket_list {
        DATE PK capture_date
        VARCHAR PK period
        INTEGER rank
        VARCHAR PK thscode
        VARCHAR ticker
        VARCHAR name
        DOUBLE heat
        INTEGER rank_change
        VARCHAR rank_trend
        JSON raw_payload
        TIMESTAMP captured_at
    }
```

## 指标（`indicators`）

1 张表。

```mermaid
erDiagram
    v_indicators_daily {
        VARCHAR PK thscode
        DATE PK date
        VARCHAR backend
        TIMESTAMP computed_at
        DOUBLE overlap_sma_5
        DOUBLE overlap_sma_10
        DOUBLE overlap_sma_20
        DOUBLE overlap_sma_60
        DOUBLE overlap_sma_120
        DOUBLE overlap_sma_250
        DOUBLE overlap_ema_5
        DOUBLE overlap_ema_10
        DOUBLE overlap_ema_20
        DOUBLE overlap_ema_60
        DOUBLE overlap_wma_20
        DOUBLE overlap_dema_20
        DOUBLE overlap_tema_20
        DOUBLE overlap_trima_20
        DOUBLE overlap_kama_14
        DOUBLE overlap_t3_5
        DOUBLE overlap_mama_mama
        DOUBLE overlap_mama_fama
        DOUBLE overlap_ht_trendline
        DOUBLE overlap_vwma_20
        DOUBLE overlap_hma_20
        DOUBLE overlap_alma_14
        DOUBLE overlap_vidya_14
        DOUBLE overlap_rma_14
        DOUBLE overlap_zlma_14
        DOUBLE overlap_mcgd_10
        DOUBLE overlap_fwma_20
        DOUBLE overlap_hwma_10
        DOUBLE overlap_jma_14
        DOUBLE overlap_pwma_14
        DOUBLE overlap_swma_10
        DOUBLE overlap_ssf_10
        DOUBLE overlap_sinwma_14
        DOUBLE momentum_rsi_6
        DOUBLE momentum_rsi_12
        DOUBLE momentum_rsi_14
        DOUBLE momentum_rsi_24
        DOUBLE momentum_macd_12_26_9_macd
        DOUBLE momentum_macd_12_26_9_signal
        DOUBLE momentum_macd_12_26_9_hist
        DOUBLE momentum_macd_5_35_5_macd
        DOUBLE momentum_macd_5_35_5_signal
        DOUBLE momentum_macd_5_35_5_hist
        DOUBLE momentum_stoch_14_3_3_slowk
        DOUBLE momentum_stoch_14_3_3_slowd
        DOUBLE momentum_stochrsi_14_fastk
        DOUBLE momentum_stochrsi_14_fastd
        DOUBLE momentum_willr_14
        DOUBLE momentum_cci_20
        DOUBLE momentum_adx_14
        DOUBLE momentum_aroon_25_aroonup
        DOUBLE momentum_aroon_25_aroondown
        DOUBLE momentum_kdj_9_3_k
        DOUBLE momentum_kdj_9_3_d
        DOUBLE momentum_kdj_9_3_j
        DOUBLE momentum_mom_10
        DOUBLE momentum_roc_10
        DOUBLE momentum_rocp_10
        DOUBLE momentum_rocr_10
        DOUBLE momentum_trix_15
        DOUBLE momentum_tsi_13_25
        DOUBLE momentum_cmo_14
        DOUBLE momentum_apo_12_26
        DOUBLE momentum_ppo_12_26
        DOUBLE momentum_stochf_5_3_fastk
        DOUBLE momentum_stochf_5_3_fastd
        DOUBLE momentum_er_10
        DOUBLE momentum_eri_13_bullp
        DOUBLE momentum_eri_13_bearp
        DOUBLE momentum_fisher_9_1_fisher
        DOUBLE momentum_fisher_9_1_signal
        DOUBLE momentum_qqe_14_5_qqe
        DOUBLE momentum_qqe_14_5_rsima
        DOUBLE momentum_qqe_14_5_long
        DOUBLE momentum_qqe_14_5_short
        DOUBLE momentum_qqe_14_5_band_long
        DOUBLE momentum_qqe_14_5_band_short
        DOUBLE momentum_qqe_14_5_diff
        DOUBLE momentum_rsx_14
        DOUBLE momentum_smi_5_20_5_smi
        DOUBLE momentum_smi_5_20_5_signal
        DOUBLE momentum_smi_5_20_5_oscillator
        DOUBLE momentum_dm_14_plus
        DOUBLE momentum_dm_14_minus
        DOUBLE momentum_brar_ar
        DOUBLE momentum_brar_br
        DOUBLE momentum_stc_line
        DOUBLE momentum_stc_macd
        DOUBLE momentum_stc_stoch
        DOUBLE momentum_lrsi_14
        DOUBLE momentum_bias_14
        DOUBLE momentum_ultosc_7_14_28
        DOUBLE momentum_ao_5_34
        DOUBLE momentum_coppock_10_10_14
        DOUBLE momentum_rvi_10_252
        DOUBLE trend_psar
        DOUBLE trend_adx_14
        DOUBLE trend_aroon_25_aroonup
        DOUBLE trend_aroon_25_aroondown
        DOUBLE trend_dpo_14
        DOUBLE trend_vortex_14_plus
        DOUBLE trend_vortex_14_minus
        DOUBLE trend_supertrend_10_3_0_trend
        DOUBLE trend_supertrend_10_3_0_direction
        DOUBLE trend_supertrend_10_3_0_long
        DOUBLE trend_supertrend_10_3_0_short
        DOUBLE trend_chop_14
        DOUBLE trend_inertia_20
        DOUBLE trend_decay_10
        DOUBLE trend_qstick_14
        DOUBLE trend_accbands_20_lower
        DOUBLE trend_accbands_20_mid
        DOUBLE trend_accbands_20_upper
        DOUBLE trend_vwmacd_12_26_9_macd
        DOUBLE trend_vwmacd_12_26_9_hist
        DOUBLE trend_vwmacd_12_26_9_signal
        DOUBLE trend_ichimoku_tenkan
        DOUBLE trend_ichimoku_kijun
        DOUBLE trend_ichimoku_senkou_a
        DOUBLE trend_ichimoku_senkou_b
        DOUBLE trend_ichimoku_chikou
        DOUBLE volatility_bbands_20_2_0_upper
        DOUBLE volatility_bbands_20_2_0_middle
        DOUBLE volatility_bbands_20_2_0_lower
        DOUBLE volatility_bbands_10_1_5_upper
        DOUBLE volatility_bbands_10_1_5_middle
        DOUBLE volatility_bbands_10_1_5_lower
        DOUBLE volatility_atr_14
        DOUBLE volatility_natr_14
        DOUBLE volatility_donchian_20_upper
        DOUBLE volatility_donchian_20_middle
        DOUBLE volatility_donchian_20_lower
        DOUBLE volatility_kc_20_2_lower
        DOUBLE volatility_kc_20_2_middle
        DOUBLE volatility_kc_20_2_upper
        DOUBLE volatility_trange
        DOUBLE volatility_vhf_14
        DOUBLE volume_obv
        DOUBLE volume_vosc_5_10
        DOUBLE volume_ha_open
        DOUBLE volume_ha_high
        DOUBLE volume_ha_low
        DOUBLE volume_ha_close
        DOUBLE volume_ad
        DOUBLE volume_adosc_3_10
        DOUBLE volume_mfi_14
        DOUBLE volume_cmf_20
        DOUBLE volume_vwap
        DOUBLE volume_pvt
        DOUBLE volume_nvi
        DOUBLE volume_pvi
        DOUBLE volume_emv
        DOUBLE volume_eom_14
        DOUBLE volume_kvo_34_55_kvo
        DOUBLE volume_kvo_34_55_signal
        DOUBLE volume_aobv_5_12_obv
        DOUBLE volume_aobv_5_12_min
        DOUBLE volume_aobv_5_12_max
        DOUBLE volume_aobv_5_12_ema5
        DOUBLE volume_aobv_5_12_ema12
        DOUBLE volume_aobv_5_12_lr
        DOUBLE volume_aobv_5_12_sr
        DOUBLE volume_vfi_13_0_5
        DOUBLE volume_wad
        DOUBLE volume_pvr
        DOUBLE cycles_ht_dcperiod
        DOUBLE cycles_ht_dcphase
        DOUBLE cycles_ht_phasor_inphase
        DOUBLE cycles_ht_phasor_quadrature
        DOUBLE cycles_ht_sine_sine
        DOUBLE cycles_ht_sine_leadsine
        DOUBLE cycles_ht_trendmode
        DOUBLE statistics_beta_20
        DOUBLE statistics_correl_20
        DOUBLE statistics_linearreg_14
        DOUBLE statistics_linearreg_angle_14
        DOUBLE statistics_linearreg_intercept_14
        DOUBLE statistics_linearreg_slope_14
        DOUBLE statistics_tsf_14
        DOUBLE statistics_stddev_20
        DOUBLE statistics_var_20
        DOUBLE statistics_entropy_10
        DOUBLE statistics_skew_30
        DOUBLE statistics_kurtosis_30
        DOUBLE statistics_zscore_20
        DOUBLE statistics_mad_20
        DOUBLE statistics_quantile_20_0_5
        DOUBLE statistics_ui_14
        DOUBLE performance_log_return_1
        DOUBLE performance_percent_return_1
        DOUBLE performance_drawdown_20_dd
        DOUBLE performance_drawdown_20_frac
        DOUBLE performance_drawdown_20_log
        DOUBLE zettaranc_zg_white_10
        DOUBLE zettaranc_dg_yellow_14
        DOUBLE zettaranc_bbi
        DOUBLE zettaranc_brick_value
        DOUBLE candles_cdl_2crows_0
        DOUBLE candles_cdl_3blackcrows_0
        DOUBLE candles_cdl_3inside_0
        DOUBLE candles_cdl_3linestrike_0
        DOUBLE candles_cdl_3outside_0
        DOUBLE candles_cdl_3starsinsouth_0
        DOUBLE candles_cdl_3whitesoldiers_0
        DOUBLE candles_cdl_abandonedbaby_0
        DOUBLE candles_cdl_advanceblock_0
        DOUBLE candles_cdl_belthold_0
        DOUBLE candles_cdl_breakaway_0
        DOUBLE candles_cdl_closingmarubozu_0
        DOUBLE candles_cdl_concealbabyswall_0
        DOUBLE candles_cdl_counterattack_0
        DOUBLE candles_cdl_darkcloudcover_0
        DOUBLE candles_cdl_doji_0
        DOUBLE candles_cdl_dojistar_0
        DOUBLE candles_cdl_dragonflydoji_0
        DOUBLE candles_cdl_engulfing_0
        DOUBLE candles_cdl_eveningdojistar_0
        DOUBLE candles_cdl_eveningstar_0
        DOUBLE candles_cdl_gapsidesidewhite_0
        DOUBLE candles_cdl_gravestonedoji_0
        DOUBLE candles_cdl_hammer_0
        DOUBLE candles_cdl_hangingman_0
        DOUBLE candles_cdl_harami_0
        DOUBLE candles_cdl_haramicross_0
        DOUBLE candles_cdl_highwave_0
        DOUBLE candles_cdl_hikkake_0
        DOUBLE candles_cdl_hikkakemod_0
        DOUBLE candles_cdl_homingpigeon_0
        DOUBLE candles_cdl_identical3crows_0
        DOUBLE candles_cdl_inneck_0
        DOUBLE candles_cdl_invertedhammer_0
        DOUBLE candles_cdl_kicking_0
        DOUBLE candles_cdl_kickingbylength_0
        DOUBLE candles_cdl_ladderbottom_0
        DOUBLE candles_cdl_longleggeddoji_0
        DOUBLE candles_cdl_longline_0
        DOUBLE candles_cdl_marubozu_0
        DOUBLE candles_cdl_matchinglow_0
        DOUBLE candles_cdl_mathold_0
        DOUBLE candles_cdl_morningdojistar_0
        DOUBLE candles_cdl_morningstar_0
        DOUBLE candles_cdl_onneck_0
        DOUBLE candles_cdl_piercing_0
        DOUBLE candles_cdl_rickshawman_0
        DOUBLE candles_cdl_risefall3methods_0
        DOUBLE candles_cdl_separatinglines_0
        DOUBLE candles_cdl_shootingstar_0
        DOUBLE candles_cdl_shortline_0
        DOUBLE candles_cdl_spinningtop_0
        DOUBLE candles_cdl_stalledpattern_0
        DOUBLE candles_cdl_sticksandwich_0
        DOUBLE candles_cdl_takuri_0
        DOUBLE candles_cdl_tasukigap_0
        DOUBLE candles_cdl_thrusting_0
        DOUBLE candles_cdl_tristar_0
        DOUBLE candles_cdl_unique3river_0
        DOUBLE candles_cdl_upsidegap2crows_0
        DOUBLE candles_cdl_xsidegap3methods_0
    }
```

## 推断关系清单

| 子表 | 父表 | 连接键 | 说明 |
|---|---|---|---|
| `raw_kline_daily` | `dim_symbol` | `thscode` | 行情 → 证券目录 |
| `calc_adjust_factor_daily` | `raw_kline_daily` | `thscode, date` | 复权因子 → 行情（同键） |
| `raw_adjustment_events` | `dim_symbol` | `thscode` | 除权事件 → 证券目录 |
| `raw_valuation_snapshot` | `dim_symbol` | `thscode` | 估值快照 → 证券目录 |
| `raw_financial_indicators` | `dim_symbol` | `thscode` | 财务指标 → 证券目录 |
| `raw_financial_indicators_detail` | `dim_symbol` | `thscode` | 财务指标明细 → 证券目录 |
| `v_indicators_daily` | `raw_kline_daily` | `thscode, date` | 指标宽表 → 行情 |

> 每一行都可以用一句 SQL 验证：
>
> ```sql
> SELECT count(*)
> FROM child c LEFT JOIN parent p USING (<连接键>)
> WHERE p.<主键> IS NULL;   -- 应为 0
> ```

