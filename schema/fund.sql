-- =============================================================================
-- fund 数据域
-- =============================================================================
-- 本文件由 scripts/export_schema.py 自动生成，请勿手工编辑。
-- 改动请改源库结构或 indicators_config.yaml，然后重新运行导出。
--
-- 导出时间基准：见 git 历史。源库中未包含任何数据行，仅含结构定义。
-- 数据版权归上游服务方所有，本项目不分发任何数据（见 docs/adr/0001）。
-- =============================================================================


-- 基表 15 张 / 视图 10 个


-- ---------- 基表 ----------

CREATE TABLE _import_batches(batch_id VARCHAR PRIMARY KEY, "source" VARCHAR NOT NULL, kind VARCHAR NOT NULL, started_at TIMESTAMP NOT NULL, finished_at TIMESTAMP, row_count BIGINT, notes VARCHAR);

CREATE TABLE _meta("key" VARCHAR PRIMARY KEY, "value" VARCHAR, updated_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_etf_daily(thscode VARCHAR, trade_date DATE, open DOUBLE, high DOUBLE, low DOUBLE, "close" DOUBLE, volume DOUBLE, turnover DOUBLE, source_batch_id VARCHAR, PRIMARY KEY(thscode, trade_date));

CREATE TABLE raw_etf_snapshot(trade_date DATE, thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, last_price DOUBLE, open DOUBLE, high DOUBLE, low DOUBLE, prev_price DOUBLE, price_change DOUBLE, price_change_ratio_pct DOUBLE, price_amplitude_ratio_pct DOUBLE, volume DOUBLE, turnover DOUBLE, turnover_ratio_pct DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(trade_date, thscode));

CREATE TABLE raw_etf_universe(thscode VARCHAR PRIMARY KEY, ticker VARCHAR, "name" VARCHAR, exchange VARCHAR, asset_type VARCHAR, list_date DATE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), estab_date_ms BIGINT);

CREATE TABLE raw_fund_company(company_id VARCHAR PRIMARY KEY, company_name VARCHAR, company_type VARCHAR, established_date_ms BIGINT, fund_count INTEGER, scale DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_fund_drawdowns(fund_thscode VARCHAR, dd_week DOUBLE, dd_month DOUBLE, dd_tmonth DOUBLE, dd_hyear DOUBLE, dd_year DOUBLE, dd_twoyear DOUBLE, dd_tyear DOUBLE, dd_fyear DOUBLE, dd_nowyear DOUBLE, dd_now DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(fund_thscode));

CREATE TABLE raw_fund_holders(fund_thscode VARCHAR, merge_scope VARCHAR, report_date_ms BIGINT, ins_position DOUBLE, holder_amount INTEGER, avg_holder_share DOUBLE, psnl_rate DOUBLE, mgmt_staff_hold_rate DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(fund_thscode, merge_scope, report_date_ms));

CREATE TABLE raw_fund_nav(thscode VARCHAR, nav_date DATE, unit_nav DOUBLE, adj_nav DOUBLE, source_batch_id VARCHAR, unit_nav_usable BOOLEAN, PRIMARY KEY(thscode, nav_date));

CREATE TABLE raw_fund_news(article_id VARCHAR PRIMARY KEY, title VARCHAR, fund_thscode VARCHAR, publish_date_ms BIGINT, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_fund_offerings(fund_thscode VARCHAR, fund_name VARCHAR, offering_start_ms BIGINT, offering_end_ms BIGINT, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(fund_thscode, offering_start_ms));

CREATE TABLE raw_fund_portfolio_holdings(fund_thscode VARCHAR, stock_thscode VARCHAR, stock_name VARCHAR, hold_ratio DOUBLE, position_count DOUBLE, security_market_value_rate_pct DOUBLE, period_increase_rate_pct DOUBLE, investment_rank INTEGER, start_date_ms BIGINT, end_date_ms BIGINT, publish_date_ms BIGINT, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(fund_thscode, stock_thscode, publish_date_ms));

CREATE TABLE raw_fund_profile(thscode VARCHAR PRIMARY KEY, ticker VARCHAR, fund_name VARCHAR, estab_date DATE, company_id VARCHAR, mgmt_name VARCHAR, manager_name VARCHAR, fund_scale DOUBLE, unit_nav DOUBLE, manager_info JSON, trade_rule JSON, rate_info JSON, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_fund_returns(fund_thscode VARCHAR, return_week DOUBLE, return_month DOUBLE, return_tmonth DOUBLE, return_hyear DOUBLE, return_year DOUBLE, return_twoyear DOUBLE, return_tyear DOUBLE, return_fyear DOUBLE, return_nowyear DOUBLE, return_now DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(fund_thscode));

CREATE TABLE raw_fund_top_holders(fund_thscode VARCHAR, holder_name VARCHAR, holder_type VARCHAR, holder_code VARCHAR, rank INTEGER, hold_share DOUBLE, hold_rate_pct DOUBLE, report_date_ms BIGINT, publish_date_ms BIGINT, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(fund_thscode, holder_name, report_date_ms));


-- ---------- 视图 ----------

CREATE VIEW v_etf_daily AS SELECT thscode, trade_date, open, high, low, "close", volume, turnover FROM raw_etf_daily;

CREATE VIEW v_etf_latest AS SELECT u.thscode, u.ticker, u."name", u.exchange, u.asset_type, s.trade_date, s.last_price, s.price_change_ratio_pct AS change_pct, s.volume, s.turnover, s.turnover_ratio_pct FROM raw_etf_universe AS u LEFT JOIN raw_etf_snapshot AS s ON (((s.thscode = u.thscode) AND (s.trade_date = (SELECT max(trade_date) FROM raw_etf_snapshot WHERE (thscode = u.thscode)))));

CREATE VIEW v_etf_universe AS SELECT thscode, ticker, "name", exchange, asset_type, list_date, estab_date_ms, CASE  WHEN ((estab_date_ms IS NOT NULL)) THEN (CAST(to_timestamp((estab_date_ms / 1000)) AS DATE)) ELSE NULL END AS estab_date, captured_at FROM raw_etf_universe;

CREATE VIEW v_fund_company AS SELECT * FROM raw_fund_company ORDER BY scale DESC NULLS LAST;

CREATE VIEW v_fund_holders AS SELECT * FROM raw_fund_holders ORDER BY fund_thscode, report_date_ms DESC;

CREATE VIEW v_fund_holdings AS SELECT * FROM raw_fund_portfolio_holdings ORDER BY fund_thscode, investment_rank;

CREATE VIEW v_fund_nav AS SELECT thscode, nav_date, unit_nav, adj_nav, unit_nav_usable FROM raw_fund_nav;

CREATE VIEW v_fund_profile AS SELECT thscode, ticker, fund_name, estab_date, company_id, mgmt_name, manager_name, fund_scale, unit_nav, captured_at FROM raw_fund_profile;

CREATE VIEW v_fund_returns AS SELECT * FROM raw_fund_returns ORDER BY return_year DESC NULLS LAST;

CREATE VIEW v_fund_top_holders AS SELECT * FROM raw_fund_top_holders ORDER BY fund_thscode, rank;
