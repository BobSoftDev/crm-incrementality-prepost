-- file: 04_silver_transforms.sql
USE CATALOG retail_crm_analytics;

-- ====== SILVER: dimensions ======
CREATE OR REPLACE TABLE `01_silver`.dim_customer AS
SELECT
  customer_id,
  CAST(signup_date AS DATE) AS signup_date,
  CAST(is_active AS INT) AS is_active,
  CAST(is_high_value AS INT) AS is_high_value,
  CAST(value_score AS DOUBLE) AS value_score,
  CAST(activity_score AS DOUBLE) AS activity_score
FROM `00_bronze`.dim_customer_bronze;

CREATE OR REPLACE TABLE `01_silver`.dim_date AS
SELECT
  CAST(date AS DATE) AS date,
  CAST(date_id AS INT) AS date_id,
  CAST(month_id AS INT) AS month_id
FROM `00_bronze`.dim_date_bronze;

-- ====== SILVER: facts ======
CREATE OR REPLACE TABLE `01_silver`.fact_transaction AS
SELECT
  transaction_id,
  customer_id,
  transaction_ts,
  channel,
  CAST(revenue AS DOUBLE) AS revenue,
  CAST(items AS INT) AS items,
  CAST(transaction_date AS DATE) AS transaction_date,
  CAST(date_id AS INT) AS date_id,
  CAST(month_id AS INT) AS month_id
FROM `00_bronze`.fact_transaction_bronze;

CREATE OR REPLACE TABLE `01_silver`.fact_crm_exposure AS
SELECT
  exposure_id,
  customer_id,
  exposure_ts,
  message_channel,
  campaign_name,
  CAST(exposure_date AS DATE) AS exposure_date,
  CAST(date_id AS INT) AS date_id,
  CAST(month_id AS INT) AS month_id
  -- NOTE: is_responder intentionally omitted from silver onward (synthetic-only)
FROM `00_bronze`.fact_crm_exposure_bronze;

-- ====== EXPOSURE ANCHOR (first exposure per customer-month) ======
CREATE OR REPLACE TABLE `01_silver`.customer_month_exposure_anchor AS
SELECT
  e.customer_id,
  e.month_id,
  MIN(e.exposure_date) AS anchor_exposure_date
FROM `01_silver`.fact_crm_exposure e
GROUP BY e.customer_id, e.month_id;

-- ====== PRE/POST WINDOW AGGREGATIONS ======
-- Baseline window = 28 days before anchor exposure
-- Post window = 7 days starting from anchor exposure
CREATE OR REPLACE TABLE `01_silver`.customer_month_pre_post AS
WITH anchors AS (
  SELECT
    customer_id,
    month_id,
    anchor_exposure_date,
    DATE_SUB(anchor_exposure_date, 28) AS pre_start,
    DATE_SUB(anchor_exposure_date, 1)  AS pre_end,
    anchor_exposure_date               AS post_start,
    DATE_ADD(anchor_exposure_date, 6)  AS post_end
  FROM `01_silver`.customer_month_exposure_anchor
),
pre_agg AS (
  SELECT
    a.customer_id,
    a.month_id,
    COUNT(DISTINCT t.transaction_id) AS pre_txn_cnt,
    SUM(t.revenue)                   AS pre_revenue,
    COUNT(DISTINCT t.transaction_date) AS pre_active_days
  FROM anchors a
  LEFT JOIN `01_silver`.fact_transaction t
    ON t.customer_id = a.customer_id
   AND t.transaction_date BETWEEN a.pre_start AND a.pre_end
  GROUP BY a.customer_id, a.month_id
),
post_agg AS (
  SELECT
    a.customer_id,
    a.month_id,
    COUNT(DISTINCT t.transaction_id) AS post_txn_cnt,
    SUM(t.revenue)                   AS post_revenue,
    COUNT(DISTINCT t.transaction_date) AS post_active_days
  FROM anchors a
  LEFT JOIN `01_silver`.fact_transaction t
    ON t.customer_id = a.customer_id
   AND t.transaction_date BETWEEN a.post_start AND a.post_end
  GROUP BY a.customer_id, a.month_id
)
SELECT
  a.customer_id,
  a.month_id,
  a.anchor_exposure_date,
  a.pre_start, a.pre_end,
  a.post_start, a.post_end,

  COALESCE(p.pre_txn_cnt, 0)        AS pre_txn_cnt,
  COALESCE(p.pre_revenue, 0.0)      AS pre_revenue,
  COALESCE(p.pre_active_days, 0)    AS pre_active_days,

  COALESCE(s.post_txn_cnt, 0)       AS post_txn_cnt,
  COALESCE(s.post_revenue, 0.0)     AS post_revenue,
  COALESCE(s.post_active_days, 0)   AS post_active_days

FROM anchors a
LEFT JOIN pre_agg p  ON p.customer_id = a.customer_id AND p.month_id = a.month_id
LEFT JOIN post_agg s ON s.customer_id = a.customer_id AND s.month_id = a.month_id;
