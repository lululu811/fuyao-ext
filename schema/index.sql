-- =============================================================================
-- index 数据域
-- =============================================================================
-- 本文件由 scripts/export_schema.py 自动生成，请勿手工编辑。
-- 改动请改源库结构或 indicators_config.yaml，然后重新运行导出。
--
-- 导出时间基准：见 git 历史。源库中未包含任何数据行，仅含结构定义。
-- 数据版权归上游服务方所有，本项目不分发任何数据（见 docs/adr/0001）。
-- =============================================================================


-- 基表 6 张 / 视图 4 个


-- ---------- 基表 ----------

CREATE TABLE _import_batches(batch_id VARCHAR PRIMARY KEY, "source" VARCHAR NOT NULL, kind VARCHAR NOT NULL, started_at TIMESTAMP NOT NULL, finished_at TIMESTAMP, row_count BIGINT, notes VARCHAR);

CREATE TABLE _meta("key" VARCHAR PRIMARY KEY, "value" VARCHAR, updated_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));

CREATE TABLE raw_index_constituents(index_thscode VARCHAR, thscode VARCHAR, ticker VARCHAR, "name" VARCHAR, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(index_thscode, thscode));

CREATE TABLE raw_index_daily(thscode VARCHAR, trade_date DATE, date_ms BIGINT, open DOUBLE, high DOUBLE, low DOUBLE, "close" DOUBLE, volume DOUBLE, turnover DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(thscode, trade_date));

CREATE TABLE raw_index_snapshot(snapshot_date DATE, thscode VARCHAR, "name" VARCHAR, last_price DOUBLE, price_change DOUBLE, price_change_ratio DOUBLE, open DOUBLE, high DOUBLE, low DOUBLE, volume DOUBLE, turnover DOUBLE, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP), PRIMARY KEY(snapshot_date, thscode));

CREATE TABLE raw_index_universe(thscode VARCHAR PRIMARY KEY, "name" VARCHAR, tag VARCHAR, raw_payload JSON, captured_at TIMESTAMP DEFAULT(CURRENT_TIMESTAMP));


-- ---------- 视图 ----------

CREATE VIEW v_index_constituents AS SELECT index_thscode, thscode, ticker, "name" FROM raw_index_constituents ORDER BY index_thscode, thscode;

CREATE VIEW v_index_daily AS SELECT * FROM raw_index_daily ORDER BY thscode, trade_date DESC;

CREATE VIEW v_index_latest AS SELECT s.* EXCLUDE ("name"), u."name" AS "name", u.tag FROM raw_index_snapshot AS s INNER JOIN (SELECT thscode, max(snapshot_date) AS max_date FROM raw_index_snapshot GROUP BY thscode) AS latest ON (((s.thscode = latest.thscode) AND (s.snapshot_date = latest.max_date))) LEFT JOIN raw_index_universe AS u ON ((s.thscode = u.thscode)) ORDER BY s.snapshot_date DESC, s.thscode;

CREATE VIEW v_index_universe AS SELECT thscode, "name", tag FROM raw_index_universe ORDER BY tag, "name";
