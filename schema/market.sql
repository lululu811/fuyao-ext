-- =============================================================================
-- market 数据域
-- =============================================================================
-- 本文件由 scripts/export_schema.py 自动生成，请勿手工编辑。
-- 改动请改源库结构或 indicators_config.yaml，然后重新运行导出。
--
-- 导出时间基准：见 git 历史。源库中未包含任何数据行，仅含结构定义。
-- 数据版权归上游服务方所有，本项目不分发任何数据（见 docs/adr/0001）。
-- =============================================================================


-- 基表 9 张 / 视图 4 个


-- ---------- 基表 ----------

CREATE TABLE _import_batches(batch_id VARCHAR PRIMARY KEY, "source" VARCHAR NOT NULL, kind VARCHAR NOT NULL, started_at TIMESTAMP NOT NULL, finished_at TIMESTAMP, row_count BIGINT, notes VARCHAR);

CREATE TABLE _meta("key" VARCHAR PRIMARY KEY, "value" VARCHAR, updated_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE calc_adjust_factor_daily(thscode VARCHAR, date DATE, forward_factor DOUBLE NOT NULL, backward_factor DOUBLE NOT NULL, factor_version VARCHAR, source_event_batch_id VARCHAR, calculated_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, date));

CREATE TABLE dim_symbol(thscode VARCHAR PRIMARY KEY, ticker VARCHAR, "name" VARCHAR, exchange VARCHAR, asset_type VARCHAR, currency VARCHAR, source_batch_id VARCHAR, updated_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_adjustment_events(thscode VARCHAR, ticker VARCHAR, ex_date DATE, dividend_per_share DOUBLE, per_share_bonus DOUBLE, allotment_ratio DOUBLE, allotment_price DOUBLE, currency VARCHAR, source_batch_id VARCHAR, PRIMARY KEY(thscode, ex_date));

CREATE TABLE raw_kline_daily(thscode VARCHAR, date DATE, open DOUBLE, high DOUBLE, low DOUBLE, "close" DOUBLE, volume DOUBLE, turnover DOUBLE, currency VARCHAR, "interval" VARCHAR, adjusted VARCHAR, source_batch_id VARCHAR, PRIMARY KEY(thscode, date));

CREATE TABLE stg_adjustment_events(thscode VARCHAR, ticker VARCHAR, ex_date DATE, dividend_per_share DOUBLE, per_share_bonus DOUBLE, allotment_ratio DOUBLE, allotment_price DOUBLE, currency VARCHAR, source_batch_id VARCHAR);

CREATE TABLE stg_kline_daily(thscode VARCHAR, date DATE, open DOUBLE, high DOUBLE, low DOUBLE, "close" DOUBLE, volume DOUBLE, turnover DOUBLE, currency VARCHAR, "interval" VARCHAR, adjusted VARCHAR, source_batch_id VARCHAR);

CREATE TABLE stg_symbols(thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, exchange VARCHAR, asset_type VARCHAR, currency VARCHAR, source_batch_id VARCHAR);


-- ---------- 视图 ----------

CREATE VIEW v_daily AS SELECT k.thscode, k.date, k.open, k.high, k.low, k."close", k.volume, k.turnover, k.currency, k."interval" FROM raw_kline_daily AS k;

CREATE VIEW v_daily_hfq AS SELECT k.thscode, k.date, (k.open * COALESCE(f.backward_factor, 1.0)) AS open, (k.high * COALESCE(f.backward_factor, 1.0)) AS high, (k.low * COALESCE(f.backward_factor, 1.0)) AS low, (k."close" * COALESCE(f.backward_factor, 1.0)) AS "close", k.volume, k.turnover, COALESCE(f.backward_factor, 1.0) AS backward_factor, k.currency, k."interval" FROM raw_kline_daily AS k LEFT JOIN calc_adjust_factor_daily AS f ON (((f.thscode = k.thscode) AND (f.date = k.date)));

CREATE VIEW v_daily_qfq AS SELECT k.thscode, k.date, (k.open * COALESCE(f.forward_factor, 1.0)) AS open, (k.high * COALESCE(f.forward_factor, 1.0)) AS high, (k.low * COALESCE(f.forward_factor, 1.0)) AS low, (k."close" * COALESCE(f.forward_factor, 1.0)) AS "close", k.volume, k.turnover, COALESCE(f.forward_factor, 1.0) AS forward_factor, k.currency, k."interval" FROM raw_kline_daily AS k LEFT JOIN calc_adjust_factor_daily AS f ON (((f.thscode = k.thscode) AND (f.date = k.date)));

CREATE VIEW v_symbol AS SELECT thscode, ticker, "name", exchange, asset_type, currency FROM dim_symbol;
