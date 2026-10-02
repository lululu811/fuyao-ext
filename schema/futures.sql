-- =============================================================================
-- futures 数据域
-- =============================================================================
-- 本文件由 scripts/export_schema.py 自动生成，请勿手工编辑。
-- 改动请改源库结构或 indicators_config.yaml，然后重新运行导出。
--
-- 导出时间基准：见 git 历史。源库中未包含任何数据行，仅含结构定义。
-- 数据版权归上游服务方所有，本项目不分发任何数据（见 docs/adr/0001）。
-- =============================================================================


-- 基表 9 张 / 视图 5 个


-- ---------- 基表 ----------

CREATE TABLE _import_batches(batch_id VARCHAR PRIMARY KEY, "source" VARCHAR NOT NULL, kind VARCHAR NOT NULL, started_at TIMESTAMP NOT NULL, finished_at TIMESTAMP, row_count BIGINT, notes VARCHAR);

CREATE TABLE _meta("key" VARCHAR PRIMARY KEY, "value" VARCHAR, updated_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_futures_basis(thscode VARCHAR, trade_date DATE, spot_price DOUBLE, converted_spot_price DOUBLE, close_price DOUBLE, settle_price DOUBLE, close_basis DOUBLE, settle_basis DOUBLE, close_basis_rate DOUBLE, settle_basis_rate DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, trade_date));

CREATE TABLE raw_futures_contracts(thscode VARCHAR PRIMARY KEY, ticker VARCHAR, "name" VARCHAR, variety_code VARCHAR, variety_name VARCHAR, exchange_code VARCHAR, list_date DATE, end_date DATE, last_trade_date DATE, last_delivery_date DATE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_futures_daily(thscode VARCHAR, trade_date DATE, open_price DOUBLE, high_price DOUBLE, low_price DOUBLE, close_price DOUBLE, volume DOUBLE, turnover DOUBLE, source_batch_id VARCHAR, PRIMARY KEY(thscode, trade_date));

CREATE TABLE raw_futures_intraday(thscode VARCHAR, trade_date DATE, "session" VARCHAR, bar_ts BIGINT, price DOUBLE, volume DOUBLE, turnover DOUBLE, source_batch_id VARCHAR, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, trade_date, "session", bar_ts));

CREATE TABLE raw_futures_positions_variety(trade_date DATE, variety_code VARCHAR, exchange_code VARCHAR, open_interest DOUBLE, open_interest_change DOUBLE, volume DOUBLE, long_open_interest DOUBLE, short_open_interest DOUBLE, long_short_ratio DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(trade_date, variety_code));

CREATE TABLE raw_futures_varieties(variety_code VARCHAR, exchange_code VARCHAR, "name" VARCHAR, quote_code VARCHAR, has_night_session BOOLEAN, margin_rate DOUBLE, main_contract_thscode VARCHAR, trade_amount VARCHAR, price_coefficient DOUBLE, price_unit VARCHAR, trade_unit VARCHAR, tick_size DOUBLE, contract_multiplier DOUBLE, capital_flow VARCHAR, long_short_ratio VARCHAR, transaction_fee VARCHAR, transaction_fee_rate VARCHAR, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(variety_code, exchange_code));

CREATE TABLE raw_futures_warehouse_receipts(thscode VARCHAR, trade_date DATE, amount DOUBLE, amount_change DOUBLE, equivalent_lots DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, trade_date));


-- ---------- 视图 ----------

CREATE VIEW v_futures_contracts AS SELECT thscode, ticker, "name", variety_code, variety_name, exchange_code, list_date, end_date, last_trade_date, last_delivery_date FROM raw_futures_contracts;

CREATE VIEW v_futures_daily AS SELECT thscode, trade_date, open_price, high_price, low_price, close_price, volume, turnover FROM raw_futures_daily;

CREATE VIEW v_futures_intraday AS SELECT thscode, trade_date, "session", bar_ts, price, volume, turnover FROM raw_futures_intraday;

CREATE VIEW v_futures_latest AS SELECT v.thscode, v.variety_code, v.exchange_code, v."name", d.trade_date, d.close_price, d.volume, d.turnover FROM v_futures_contracts AS v INNER JOIN (SELECT trade_date, close_price, volume, turnover FROM raw_futures_daily AS d WHERE (d.thscode = v.thscode) ORDER BY trade_date DESC LIMIT 1) AS d ON (CAST('t' AS BOOLEAN));

CREATE VIEW v_futures_varieties AS SELECT variety_code, exchange_code, "name", has_night_session, margin_rate, main_contract_thscode, trade_unit, tick_size, contract_multiplier FROM raw_futures_varieties;
