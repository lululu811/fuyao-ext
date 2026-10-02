-- =============================================================================
-- special 数据域
-- =============================================================================
-- 本文件由 scripts/export_schema.py 自动生成，请勿手工编辑。
-- 改动请改源库结构或 indicators_config.yaml，然后重新运行导出。
--
-- 导出时间基准：见 git 历史。源库中未包含任何数据行，仅含结构定义。
-- 数据版权归上游服务方所有，本项目不分发任何数据（见 docs/adr/0001）。
-- =============================================================================


-- 基表 13 张 / 视图 11 个


-- ---------- 基表 ----------

CREATE TABLE _import_batches(batch_id VARCHAR PRIMARY KEY, "source" VARCHAR NOT NULL, kind VARCHAR NOT NULL, started_at TIMESTAMP NOT NULL, finished_at TIMESTAMP, row_count BIGINT, notes VARCHAR);

CREATE TABLE _meta("key" VARCHAR PRIMARY KEY, "value" VARCHAR, updated_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_anomaly_list(capture_date DATE, thscode VARCHAR, stock_name VARCHAR, tag_name VARCHAR, analysis_content VARCHAR, keyword_list JSON, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(capture_date, thscode, tag_name));

CREATE TABLE raw_auction_benchmark(benchmark_date DATE, thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, auction_pct DOUBLE, tags VARCHAR, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(benchmark_date, thscode));

CREATE TABLE raw_auction_snapshot(snapshot_date DATE, thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, auction_price DOUBLE, auction_pct DOUBLE, auction_volume DOUBLE, auction_amount DOUBLE, auction_unmatched DOUBLE, auction_turnover_pct DOUBLE, auction_yesterday_ratio_pct DOUBLE, auction_volume_ratio DOUBLE, pre_close_price DOUBLE, open_price DOUBLE, last_price DOUBLE, float_market_cap DOUBLE, stage VARCHAR, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(snapshot_date, thscode, stage));

CREATE TABLE raw_dragon_tiger(trade_date DATE, board_type VARCHAR, thscode VARCHAR, "name" VARCHAR, net_value DOUBLE, net_rate DOUBLE, buy_value DOUBLE, sell_value DOUBLE, org_net_value DOUBLE, change DOUBLE, hot_rank INTEGER, range_days INTEGER, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(trade_date, board_type, thscode));

CREATE TABLE raw_hot_stock_history(history_date DATE, rank INTEGER, thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(history_date, thscode));

CREATE TABLE raw_hot_stock_list(capture_date DATE, period VARCHAR, rank INTEGER, thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, heat DOUBLE, rank_change INTEGER, rank_trend VARCHAR, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(capture_date, period, thscode));

CREATE TABLE raw_hot_stock_rank_trend(thscode VARCHAR, trend_date DATE, date_ms BIGINT, rank INTEGER, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, trend_date));

CREATE TABLE raw_limit_break_pool(trade_date DATE, thscode VARCHAR, "name" VARCHAR, last_price DOUBLE, open_times INTEGER, price_change_ratio DOUBLE, turnover DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(trade_date, thscode));

CREATE TABLE raw_limit_down_pool(trade_date DATE, thscode VARCHAR, "name" VARCHAR, last_price DOUBLE, price_change_ratio DOUBLE, first_limit_time VARCHAR, last_limit_time VARCHAR, turnover_ratio DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(trade_date, thscode));

CREATE TABLE raw_limit_up_pool(trade_date DATE, thscode VARCHAR, "name" VARCHAR, last_price DOUBLE, continue_day_cnt INTEGER, limit_up_time VARCHAR, seal_money DOUBLE, turnover_ratio DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(trade_date, thscode));

CREATE TABLE raw_skyrocket_list(capture_date DATE, period VARCHAR, rank INTEGER, thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, heat DOUBLE, rank_change INTEGER, rank_trend VARCHAR, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(capture_date, period, thscode));


-- ---------- 视图 ----------

CREATE VIEW v_anomaly_list AS SELECT * FROM raw_anomaly_list ORDER BY capture_date DESC, tag_name, thscode;

CREATE VIEW v_auction_benchmark AS SELECT * FROM raw_auction_benchmark ORDER BY benchmark_date DESC, auction_pct DESC;

CREATE VIEW v_auction_snapshot AS SELECT * FROM raw_auction_snapshot ORDER BY snapshot_date DESC, auction_pct DESC;

CREATE VIEW v_dragon_tiger AS SELECT trade_date, board_type, thscode, "name", net_value, net_rate, buy_value, sell_value, org_net_value, change, hot_rank, range_days FROM raw_dragon_tiger ORDER BY trade_date DESC, abs(net_value) DESC;

CREATE VIEW v_hot_stock AS SELECT * FROM raw_hot_stock_list ORDER BY capture_date DESC, period, rank;

CREATE VIEW v_hot_stock_history AS SELECT * FROM raw_hot_stock_history ORDER BY history_date DESC, rank;

CREATE VIEW v_hot_stock_rank_trend AS SELECT * FROM raw_hot_stock_rank_trend ORDER BY thscode, trend_date DESC;

CREATE VIEW v_limit_break_pool AS SELECT trade_date, thscode, "name", last_price, open_times, price_change_ratio FROM raw_limit_break_pool ORDER BY trade_date, open_times DESC;

CREATE VIEW v_limit_down_pool AS SELECT trade_date, thscode, "name", last_price, price_change_ratio, first_limit_time, last_limit_time FROM raw_limit_down_pool ORDER BY trade_date DESC;

CREATE VIEW v_limit_up_pool AS SELECT trade_date, thscode, "name", last_price, continue_day_cnt, limit_up_time, seal_money FROM raw_limit_up_pool ORDER BY trade_date DESC, continue_day_cnt DESC;

CREATE VIEW v_skyrocket AS SELECT * FROM raw_skyrocket_list ORDER BY capture_date DESC, rank;
