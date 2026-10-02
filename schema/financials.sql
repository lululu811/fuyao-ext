-- =============================================================================
-- financials 数据域
-- =============================================================================
-- 本文件由 scripts/export_schema.py 自动生成，请勿手工编辑。
-- 改动请改源库结构或 indicators_config.yaml，然后重新运行导出。
--
-- 导出时间基准：见 git 历史。源库中未包含任何数据行，仅含结构定义。
-- 数据版权归上游服务方所有，本项目不分发任何数据（见 docs/adr/0001）。
-- =============================================================================


-- 基表 9 张 / 视图 7 个


-- ---------- 基表 ----------

CREATE TABLE _import_batches(batch_id VARCHAR PRIMARY KEY, "source" VARCHAR NOT NULL, kind VARCHAR NOT NULL, started_at TIMESTAMP NOT NULL, finished_at TIMESTAMP, row_count BIGINT, notes VARCHAR);

CREATE TABLE _meta("key" VARCHAR PRIMARY KEY, "value" VARCHAR, updated_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_balance_sheet(thscode VARCHAR, period VARCHAR, period_end_ms BIGINT, report_date_ms BIGINT, fiscal_year INTEGER, fiscal_period VARCHAR, currency VARCHAR, total_current_assets DOUBLE, non_current_nets_total DOUBLE, assets_total DOUBLE, total_debt DOUBLE, holder_equity_total DOUBLE, cash DOUBLE, accounts_receivable DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, period, period_end_ms));

CREATE TABLE raw_cash_flow_statement(thscode VARCHAR, period VARCHAR, period_end_ms BIGINT, report_date_ms BIGINT, fiscal_year INTEGER, fiscal_period VARCHAR, currency VARCHAR, act_cash_flow_net DOUBLE, invest_cash_flow_net DOUBLE, financing_cash_flow_net DOUBLE, cash_equivalents_net_addition DOUBLE, pay_dividends_profits_interest_cash DOUBLE, pay_fixed_assets_etc_cash DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, period, period_end_ms));

CREATE TABLE raw_financial_indicators(thscode VARCHAR, report VARCHAR, abilities_json JSON, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, report));

CREATE TABLE raw_financial_indicators_detail(thscode VARCHAR, report VARCHAR, operating_income_yoy DOUBLE, operating_profit_yoy DOUBLE, total_assets_growth_ratio DOUBLE, fixed_asset_invest_expansion_ratio DOUBLE, parent_holder_net_profit_yoy DOUBLE, total_assets_net_ratio DOUBLE, deduct_weighted_avg_roe DOUBLE, sale_gross_margin DOUBLE, sale_net_interest_ratio DOUBLE, weighted_avg_roe DOUBLE, current_ratio DOUBLE, cash_ratio DOUBLE, quick_ratio DOUBLE, earned_interest_multiple DOUBLE, assets_debt_ratio DOUBLE, total_assets_turnover_ratio DOUBLE, inventory_turnover_ratio DOUBLE, long_term_debt_equity_ratio DOUBLE, current_assets_turnover_ratio DOUBLE, receive_account_turnover_ratio DOUBLE, net_profit_cash_content DOUBLE, cash_operating_index DOUBLE, operating_cash_flow_net_divide_income DOUBLE, cash_meet_invest_ratio DOUBLE, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, report));

CREATE TABLE raw_income_statement(thscode VARCHAR, period VARCHAR, period_end_ms BIGINT, report_date_ms BIGINT, fiscal_year INTEGER, fiscal_period VARCHAR, currency VARCHAR, basic_eps DOUBLE, operating_income DOUBLE, operating_costs DOUBLE, operating_expenses DOUBLE, operating_profit DOUBLE, profit_total DOUBLE, net_profit DOUBLE, parent_holder_net_profit DOUBLE, income_tax_expense DOUBLE, interest_expenses DOUBLE, manage_fee DOUBLE, sales_fee DOUBLE, research_and_development_expenses DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, period, period_end_ms));

CREATE TABLE raw_trading_calendar(trade_date DATE PRIMARY KEY, date_ms BIGINT NOT NULL, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_valuation_snapshot(snapshot_date DATE, thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, pe_ttm DOUBLE, pe_mrq DOUBLE, pb_mrq DOUBLE, ps_ttm DOUBLE, pcf_ttm DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(snapshot_date, thscode));


-- ---------- 视图 ----------

CREATE VIEW v_balance_sheet AS SELECT * FROM raw_balance_sheet ORDER BY thscode, period, period_end_ms DESC;

CREATE VIEW v_cash_flow_statement AS SELECT * FROM raw_cash_flow_statement ORDER BY thscode, period, period_end_ms DESC;

CREATE VIEW v_financial_indicators AS SELECT thscode, report, abilities_json, captured_at FROM raw_financial_indicators ORDER BY thscode, report DESC;

CREATE VIEW v_financial_indicators_detail AS SELECT * FROM raw_financial_indicators_detail ORDER BY thscode, report DESC;

CREATE VIEW v_income_statement AS SELECT * FROM raw_income_statement ORDER BY thscode, period, period_end_ms DESC;

CREATE VIEW v_trading_calendar AS SELECT trade_date, date_ms FROM raw_trading_calendar ORDER BY trade_date;

CREATE VIEW v_valuation_latest AS SELECT v.* FROM raw_valuation_snapshot AS v INNER JOIN (SELECT thscode, max(snapshot_date) AS max_date FROM raw_valuation_snapshot GROUP BY thscode) AS latest ON (((v.thscode = latest.thscode) AND (v.snapshot_date = latest.max_date)));
