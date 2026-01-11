-- file: 05_gold_incrementality.sql
-- Purpose: Build Gold incrementality + robust RFM that tolerates month_id formats (yyyyMM or yyyyMMdd)

USE CATALOG retail_crm_analytics;

-- =========================================================
-- 1) FACT: customer-month incrementality (no changes needed)
--    (kept as you had it, but we add a stable month_key_yyyymm)
-- =========================================================

CREATE OR REPLACE TABLE `02_gold`.fact_customer_month_incrementality AS
WITH base AS (
  SELECT
    c.customer_id,
    x.month_id,
    x.anchor_exposure_date,

    c.is_active,
    c.is_high_value,

    x.pre_txn_cnt,
    x.pre_revenue,
    x.pre_active_days,

    x.post_txn_cnt,
    x.post_revenue,
    x.post_active_days,

    28 AS pre_days,
    7  AS post_days
  FROM `01_silver`.customer_month_pre_post x
  JOIN `01_silver`.dim_customer c
    ON c.customer_id = x.customer_id
),
month_norm AS (
  SELECT
    *,
    /* month_id može biti yyyyMM ili yyyyMMdd; normalizujemo u yyyyMM (INT) */
    CASE
      WHEN month_id IS NULL THEN NULL
      WHEN CAST(month_id AS STRING) RLIKE '^[0-9]{6}$' THEN CAST(month_id AS INT)                   -- yyyyMM
      WHEN CAST(month_id AS STRING) RLIKE '^[0-9]{8}$' THEN CAST(SUBSTR(CAST(month_id AS STRING),1,6) AS INT) -- yyyyMMdd -> yyyyMM
      ELSE NULL
    END AS month_key_yyyymm
  FROM base
),
kpis AS (
  SELECT
    *,
    CASE WHEN pre_days > 0 THEN pre_revenue / pre_days ELSE 0.0 END  AS pre_rev_per_day,
    CASE WHEN post_days > 0 THEN post_revenue / post_days ELSE 0.0 END AS post_rev_per_day,

    CASE WHEN pre_days > 0 THEN pre_txn_cnt / pre_days ELSE 0.0 END  AS pre_txn_per_day,
    CASE WHEN post_days > 0 THEN post_txn_cnt / post_days ELSE 0.0 END AS post_txn_per_day,

    CASE WHEN pre_days > 0 THEN pre_active_days / pre_days ELSE 0.0 END  AS pre_freq,
    CASE WHEN post_days > 0 THEN post_active_days / post_days ELSE 0.0 END AS post_freq,

    CASE
      WHEN (CASE WHEN pre_days > 0 THEN pre_txn_cnt / pre_days ELSE 0.0 END) > 0
      THEN (pre_revenue / pre_days) / (pre_txn_cnt / pre_days)
      ELSE 0.0
    END AS pre_aov,

    CASE
      WHEN (CASE WHEN post_days > 0 THEN post_txn_cnt / post_days ELSE 0.0 END) > 0
      THEN (post_revenue / post_days) / (post_txn_cnt / post_days)
      ELSE 0.0
    END AS post_aov
  FROM month_norm
)
SELECT
  customer_id,
  month_id,
  month_key_yyyymm,
  anchor_exposure_date,

  is_active,
  is_high_value,

  pre_txn_cnt,
  pre_revenue,
  pre_active_days,
  post_txn_cnt,
  post_revenue,
  post_active_days,

  pre_rev_per_day,
  post_rev_per_day,
  pre_txn_per_day,
  post_txn_per_day,
  pre_freq,
  post_freq,
  pre_aov,
  post_aov,

  (post_rev_per_day - pre_rev_per_day) * 7 AS incremental_revenue,
  (post_txn_per_day - pre_txn_per_day) * 7 AS incremental_transactions,
  (post_freq - pre_freq) * 7              AS incremental_freq_points,
  (post_aov - pre_aov)                    AS delta_aov
FROM kpis;

-- =========================================================
-- 2) RFM: robust month end derivation (FIXED)
--    Problem was parsing month_id incorrectly.
--    We derive month_end using:
--      a) try_to_date(yyyyMM01)
--      b) or try_to_date(yyyyMMdd) then truncate to month
-- =========================================================

CREATE OR REPLACE TABLE `02_gold`.dim_customer_month_rfm AS
WITH month_candidates AS (
  SELECT DISTINCT
    month_id,
    CASE
      WHEN month_id IS NULL THEN NULL

      -- If month_id is yyyyMM (e.g., 202501), create yyyyMM01
      WHEN CAST(month_id AS STRING) RLIKE '^[0-9]{6}$'
        THEN TRY_TO_DATE(CONCAT(CAST(month_id AS STRING), '01'), 'yyyyMMdd')

      -- If month_id is yyyyMMdd (e.g., 20250101), parse directly
      WHEN CAST(month_id AS STRING) RLIKE '^[0-9]{8}$'
        THEN TRY_TO_DATE(CAST(month_id AS STRING), 'yyyyMMdd')

      ELSE NULL
    END AS any_date_in_month
  FROM `01_silver`.dim_date
),
month_ends AS (
  SELECT
    month_id,
    /* Take parsed date, truncate to month, then month end */
    CASE
      WHEN any_date_in_month IS NULL THEN NULL
      ELSE LAST_DAY(DATE_TRUNC('MONTH', any_date_in_month))
    END AS month_end
  FROM month_candidates
),
windowed AS (
  SELECT
    t.customer_id,
    m.month_id,
    m.month_end,
    MAX(t.transaction_date) AS last_purchase_date,
    COUNT(*) AS txns_90d,
    SUM(t.revenue) AS rev_90d
  FROM month_ends m
  LEFT JOIN `01_silver`.fact_transaction t
    ON m.month_end IS NOT NULL
   AND t.transaction_date BETWEEN DATE_SUB(m.month_end, 89) AND m.month_end
  GROUP BY t.customer_id, m.month_id, m.month_end
),
scored AS (
  SELECT
    customer_id,
    month_id,
    CASE
      WHEN last_purchase_date IS NULL OR month_end IS NULL THEN 999
      ELSE DATEDIFF(month_end, last_purchase_date)
    END AS recency_days,
    COALESCE(txns_90d, 0) AS frequency_90d,
    COALESCE(rev_90d, 0.0) AS monetary_90d
  FROM windowed
),
bucketed AS (
  SELECT
    customer_id,
    month_id,
    recency_days,
    frequency_90d,
    monetary_90d,
    NTILE(5) OVER (PARTITION BY month_id ORDER BY recency_days ASC)      AS r_score,
    NTILE(5) OVER (PARTITION BY month_id ORDER BY frequency_90d ASC)    AS f_score,
    NTILE(5) OVER (PARTITION BY month_id ORDER BY monetary_90d ASC)     AS m_score
  FROM scored
)
SELECT
  customer_id,
  month_id,
  r_score,
  f_score,
  m_score,
  CONCAT('R', r_score, 'F', f_score, 'M', m_score) AS rfm_code,
  CASE
    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
    WHEN r_score >= 4 AND f_score >= 3 THEN 'Loyal'
    WHEN r_score >= 3 AND f_score >= 3 THEN 'Potential Loyalists'
    WHEN r_score <= 2 AND f_score <= 2 THEN 'At Risk'
    WHEN r_score = 1 THEN 'Lost'
    ELSE 'Others'
  END AS rfm_segment
FROM bucketed;

-- =========================================================
-- 3) GOLD SUMMARY TABLES (use month_key_yyyymm where helpful)
-- =========================================================

CREATE OR REPLACE TABLE `02_gold`.agg_incrementality_month AS
SELECT
  month_key_yyyymm AS month_id,
  COUNT(DISTINCT customer_id) AS exposed_customer_months,
  SUM(incremental_revenue) AS incremental_revenue,
  SUM(incremental_transactions) AS incremental_transactions,
  AVG(delta_aov) AS avg_delta_aov
FROM `02_gold`.fact_customer_month_incrementality
GROUP BY month_key_yyyymm;

CREATE OR REPLACE TABLE `02_gold`.agg_incrementality_rfm AS
SELECT
  f.month_key_yyyymm AS month_id,
  r.rfm_segment,
  COUNT(DISTINCT f.customer_id) AS customers,
  SUM(f.incremental_revenue) AS incremental_revenue,
  SUM(f.incremental_transactions) AS incremental_transactions,
  AVG(f.delta_aov) AS avg_delta_aov
FROM `02_gold`.fact_customer_month_incrementality f
LEFT JOIN `02_gold`.dim_customer_month_rfm r
  ON r.customer_id = f.customer_id
 AND r.month_id = f.month_id
GROUP BY f.month_key_yyyymm, r.rfm_segment;

CREATE OR REPLACE TABLE `02_gold`.agg_incrementality_active_value AS
SELECT
  month_key_yyyymm AS month_id,
  is_active,
  is_high_value,
  COUNT(DISTINCT customer_id) AS customers,
  SUM(incremental_revenue) AS incremental_revenue,
  SUM(incremental_transactions) AS incremental_transactions,
  AVG(delta_aov) AS avg_delta_aov
FROM `02_gold`.fact_customer_month_incrementality
GROUP BY month_key_yyyymm, is_active, is_high_value;
