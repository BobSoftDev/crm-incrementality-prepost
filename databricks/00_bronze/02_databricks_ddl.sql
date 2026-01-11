-- file: 02_databricks_ddl.sql
-- Purpose: Create catalog, schemas (00_bronze/01_silver/02_gold), volumes, and tables.

-- ====== CONFIG (edit names) ======
CREATE CATALOG IF NOT EXISTS retail_crm_analytics;

USE CATALOG retail_crm_analytics;

CREATE SCHEMA IF NOT EXISTS `00_bronze`;
CREATE SCHEMA IF NOT EXISTS `01_silver`;
CREATE SCHEMA IF NOT EXISTS `02_gold`;

-- ====== VOLUMES (Unity Catalog Volumes) ======
-- If your workspace uses external locations, ensure permissions exist.
CREATE VOLUME IF NOT EXISTS `00_bronze`.vol_input;
CREATE VOLUME IF NOT EXISTS `02_gold`.vol_export;

-- ====== BRONZE TABLES ======
CREATE TABLE IF NOT EXISTS `00_bronze`.dim_customer_bronze (
  customer_id        BIGINT,
  signup_date        DATE,
  is_active          INT,
  is_high_value      INT,
  value_score        DOUBLE,
  activity_score     DOUBLE
)
USING DELTA;

CREATE TABLE IF NOT EXISTS `00_bronze`.dim_date_bronze (
  date              DATE,
  date_id           INT,
  month_id          INT
)
USING DELTA;

CREATE TABLE IF NOT EXISTS `00_bronze`.fact_transaction_bronze (
  transaction_id    BIGINT,
  customer_id       BIGINT,
  transaction_ts    TIMESTAMP,
  channel           STRING,
  revenue           DOUBLE,
  items             INT,
  transaction_date  DATE,
  date_id           INT,
  month_id          INT
)
USING DELTA;

CREATE TABLE IF NOT EXISTS `00_bronze`.fact_crm_exposure_bronze (
  exposure_id       BIGINT,
  customer_id       BIGINT,
  exposure_ts       TIMESTAMP,
  message_channel   STRING,
  campaign_name     STRING,
  is_responder      INT,        -- synthetic truth only; drop in real implementations
  exposure_date     DATE,
  date_id           INT,
  month_id          INT
)
USING DELTA;
