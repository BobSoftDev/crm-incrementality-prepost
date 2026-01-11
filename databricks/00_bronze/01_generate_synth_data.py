# file: 01_generate_synth_data.py
# Purpose: Generate realistic synthetic omnichannel CRM + transactions data locally.
# Output: CSV files in ./data_synth/

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

SEED = 42
np.random.seed(SEED)

OUT_DIR = os.path.join(os.getcwd(), "data_synth")
os.makedirs(OUT_DIR, exist_ok=True)

# ---- Config (edit as needed) ----
N_CUSTOMERS = 50000
START_DATE = pd.Timestamp("2025-01-01")
END_DATE   = pd.Timestamp("2025-12-31")  
CHANNELS = ["offline", "online"]

# Exposure behavior
EXPOSURE_BASE_RATE = 0.18  # average monthly probability of exposure per customer
EXPOSURE_BIAS_ACTIVE = 1.6 # active customers more likely targeted
EXPOSURE_BIAS_HV = 1.4     # high-value customers more likely targeted

# Impact modeling
IMPACT_WINDOW_DAYS = 7
BASELINE_WINDOW_DAYS = 28
LIFT_MEAN = 0.06           # average uplift in revenue/day for responders
LIFT_STD  = 0.05
RESPONDER_RATE = 0.35      # fraction of exposed customers that truly respond

# ---- Helper ----
def daterange(start, end):
    return pd.date_range(start=start, end=end, freq="D")

dates = daterange(START_DATE, END_DATE)
date_df = pd.DataFrame({"date": dates})
date_df["date_id"] = date_df["date"].dt.strftime("%Y%m%d").astype(int)
date_df["month_id"] = date_df["date"].dt.strftime("%Y%m").astype(int)

# ---- Customers ----
cust = pd.DataFrame({
    "customer_id": np.arange(1, N_CUSTOMERS + 1),
})
cust["signup_date"] = START_DATE + pd.to_timedelta(np.random.randint(0, 180, size=N_CUSTOMERS), unit="D")

# Latent value & activity propensities
cust["value_score"] = np.clip(np.random.normal(0.0, 1.0, size=N_CUSTOMERS), -2.5, 2.5)
cust["activity_score"] = np.clip(np.random.normal(0.0, 1.0, size=N_CUSTOMERS), -2.5, 2.5)

# High-value flag (top ~30%)
hv_threshold = np.quantile(cust["value_score"], 0.70)
cust["is_high_value"] = (cust["value_score"] >= hv_threshold).astype(int)

# Active flag (top ~50% by activity score)
act_threshold = np.quantile(cust["activity_score"], 0.50)
cust["is_active"] = (cust["activity_score"] >= act_threshold).astype(int)

# ---- Transactions ----
# We simulate daily purchase probability driven by activity_score and seasonality
base_p = 0.015  # base daily purchase probability
seasonality = (np.sin(np.linspace(0, 6*np.pi, len(dates))) + 1.0) / 2.0  # 0..1

tx_rows = []
tx_id = 1

for d_i, d in enumerate(dates):
    seas = seasonality[d_i]
    # daily purchase probability per customer
    # logistic-ish transform to keep probabilities reasonable
    p = base_p * (1.0 + 0.9*seas) * np.exp(0.45*cust["activity_score"].values)
    p = np.clip(p, 0.0005, 0.12)

    buy = np.random.rand(N_CUSTOMERS) < p
    buyers = cust.loc[buy, ["customer_id", "value_score"]].copy()
    if buyers.empty:
        continue

    # transactions per buying customer: mostly 1, sometimes 2
    n_tx = 1 + (np.random.rand(len(buyers)) < 0.08).astype(int)

    # revenue per txn depends on value_score
    # lognormal for realistic skew
    mu = 3.3 + 0.35*buyers["value_score"].values
    sigma = 0.55
    for idx, row in buyers.iterrows():
        for _ in range(int(n_tx[buyers.index.get_loc(idx)])):
            channel = np.random.choice(CHANNELS, p=[0.72, 0.28])
            revenue = float(np.random.lognormal(mean=mu[buyers.index.get_loc(idx)], sigma=sigma))
            items = int(np.clip(np.random.poisson(lam=3.2), 1, 25))
            tx_rows.append({
                "transaction_id": tx_id,
                "customer_id": int(row["customer_id"]),
                "transaction_ts": pd.Timestamp(d) + pd.to_timedelta(np.random.randint(0, 86400), unit="s"),
                "channel": channel,
                "revenue": round(revenue, 2),
                "items": items,
            })
            tx_id += 1

tx = pd.DataFrame(tx_rows)
if tx.empty:
    raise RuntimeError("No transactions generated. Adjust probabilities.")

tx["transaction_date"] = tx["transaction_ts"].dt.floor("D")
tx = tx.merge(date_df[["date", "date_id", "month_id"]], left_on="transaction_date", right_on="date", how="left")
tx.drop(columns=["date"], inplace=True)

# ---- CRM Exposures ----
# monthly exposure probability influenced by is_active and is_high_value
months = pd.period_range(START_DATE, END_DATE, freq="M").astype(str)
exp_rows = []
exp_id = 1

for m in months:
    m_start = pd.Timestamp(m + "-01")
    m_end = (m_start + pd.offsets.MonthEnd(1)).normalize()
    month_days = pd.date_range(m_start, min(m_end, END_DATE), freq="D")

    # monthly targeting propensity
    base = EXPOSURE_BASE_RATE
    prob = base \
        * (1.0 + (EXPOSURE_BIAS_ACTIVE - 1.0)*cust["is_active"].values) \
        * (1.0 + (EXPOSURE_BIAS_HV - 1.0)*cust["is_high_value"].values)
    prob = np.clip(prob, 0.02, 0.75)

    exposed = np.random.rand(N_CUSTOMERS) < prob
    targets = cust.loc[exposed, ["customer_id", "is_active", "is_high_value"]].copy()
    if targets.empty:
        continue

    # choose an exposure day/time in the month
    chosen_days = np.random.choice(month_days, size=len(targets), replace=True)
    chosen_times = pd.to_timedelta(np.random.randint(8*3600, 20*3600, size=len(targets)), unit="s")
    exp_ts = pd.to_datetime(chosen_days) + chosen_times

    # responder flag (true underlying lift)
    responders = (np.random.rand(len(targets)) < RESPONDER_RATE).astype(int)

    # channel and campaign
    msg_channel = np.random.choice(["email", "sms", "push"], size=len(targets), p=[0.55, 0.25, 0.20])
    campaign = np.random.choice(["Promo_A", "Promo_B", "Reactivation", "CrossSell"], size=len(targets), p=[0.35, 0.25, 0.20, 0.20])

    for i, (cid, ts_val, ch, camp, resp) in enumerate(zip(
        targets["customer_id"].values, exp_ts, msg_channel, campaign, responders
    )):
        exp_rows.append({
            "exposure_id": exp_id,
            "customer_id": int(cid),
            "exposure_ts": pd.Timestamp(ts_val),
            "message_channel": ch,
            "campaign_name": camp,
            "is_responder": int(resp)  # latent for synthetic truth; NOT used in real life
        })
        exp_id += 1

exp = pd.DataFrame(exp_rows)
exp["exposure_date"] = exp["exposure_ts"].dt.floor("D")
exp = exp.merge(date_df[["date", "date_id", "month_id"]], left_on="exposure_date", right_on="date", how="left")
exp.drop(columns=["date"], inplace=True)

# ---- Inject uplift into transactions for responders (synthetic effect) ----
# For each responder exposure, increase spend probability / revenue in post 7 days
# We will do it by multiplying revenue for transactions in post window by a factor.
if not exp.empty and not tx.empty:
    # Build mapping of responder exposures
    responder_exp = exp.loc[exp["is_responder"] == 1, ["customer_id", "exposure_date"]].copy()
    responder_exp["post_start"] = responder_exp["exposure_date"]
    responder_exp["post_end"] = responder_exp["exposure_date"] + pd.to_timedelta(IMPACT_WINDOW_DAYS - 1, unit="D")

    # For efficiency, sample a subset of effects
    # Apply revenue multiplier on tx in window for those customers
    tx["revenue_adj"] = tx["revenue"].astype(float)

    # Create a lookup by customer for multiple windows (simple loop; ok for 5k customers)
    for _, r in responder_exp.iterrows():
        cid = int(r["customer_id"])
        mask = (tx["customer_id"] == cid) & (tx["transaction_date"] >= r["post_start"]) & (tx["transaction_date"] <= r["post_end"])
        if mask.any():
            lift = float(np.clip(np.random.normal(LIFT_MEAN, LIFT_STD), 0.0, 0.25))
            tx.loc[mask, "revenue_adj"] = (tx.loc[mask, "revenue_adj"] * (1.0 + lift)).round(2)

    tx["revenue"] = tx["revenue_adj"]
    tx.drop(columns=["revenue_adj"], inplace=True)

# ---- Save files ----
cust_out = cust[["customer_id", "signup_date", "is_active", "is_high_value", "value_score", "activity_score"]].copy()
cust_out.to_csv(os.path.join(OUT_DIR, "dim_customer.csv"), index=False)

date_df.to_csv(os.path.join(OUT_DIR, "dim_date.csv"), index=False)
tx.to_csv(os.path.join(OUT_DIR, "fact_transaction.csv"), index=False)
exp.to_csv(os.path.join(OUT_DIR, "fact_crm_exposure.csv"), index=False)

print("Synthetic data generated to:", OUT_DIR)
print("Rows:", {
    "customers": len(cust_out),
    "dates": len(date_df),
    "transactions": len(tx),
    "exposures": len(exp),
})
