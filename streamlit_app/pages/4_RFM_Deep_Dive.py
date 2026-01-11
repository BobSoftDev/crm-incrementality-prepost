import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data import (
    get_default_export_folder,
    load_csv_folder,
    ensure_month_fields,
    sort_month
)
from utils.narrative import render_narrative, narrative_rfm

st.title("RFM Deep Dive")

folder = st.sidebar.text_input("Gold export folder", value=get_default_export_folder())

rfm = load_csv_folder(folder, "agg_incrementality_rfm.csv")
rfm = ensure_month_fields(rfm, "month_id")
rfm = sort_month(rfm)
rfm = rfm.fillna({"rfm_segment": "Unknown"})

# ---- Ensure numeric types (robust) ----
for col in ["incremental_revenue", "customers", "incremental_transactions", "avg_delta_aov"]:
    if col in rfm.columns:
        rfm[col] = pd.to_numeric(rfm[col], errors="coerce").fillna(0.0)

# ---- Month selector ----
months = [m for m in rfm["month_id_norm"].unique().tolist() if m != "Unknown"]
months = sorted(months)
sel_month = st.selectbox("Select month", months, index=(len(months) - 1) if len(months) else 0)

# ---- Filter to selected month FIRST ----
rfm_month = rfm[rfm["month_id_norm"] == sel_month].copy()

# ---- Aggregate to one row per segment per month ----
m = rfm_month.groupby(["month_id_norm", "month_label", "rfm_segment"], as_index=False).agg(
    incremental_revenue=("incremental_revenue", "sum"),
    customers=("customers", "sum"),
    incremental_transactions=("incremental_transactions", "sum"),
    avg_delta_aov=("avg_delta_aov", "mean"),
)

# ---- Sort for top/bottom ----
m = m.sort_values("incremental_revenue", ascending=False)

# ---- KPIs (net + decomposition) ----
total_rev_net = float(m["incremental_revenue"].sum()) if len(m) else 0.0

total_rev_pos = float(m.loc[m["incremental_revenue"] > 0, "incremental_revenue"].sum()) if len(m) else 0.0
total_rev_neg = float(m.loc[m["incremental_revenue"] < 0, "incremental_revenue"].sum()) if len(m) else 0.0  # negative value

top_seg = str(m.iloc[0]["rfm_segment"]) if len(m) else "N/A"
top_rev = float(m.iloc[0]["incremental_revenue"]) if len(m) else 0.0

bottom_seg = str(m.iloc[-1]["rfm_segment"]) if len(m) else None
bottom_rev = float(m.iloc[-1]["incremental_revenue"]) if len(m) else None

# Shares:
# - Share of NET can exceed 100% when negatives exist (this is OK).
share_of_net = (top_rev / total_rev_net) if total_rev_net != 0 else None
# - Share of POSITIVE contributions is the executive-friendly concentration metric.
share_of_positive = (top_rev / total_rev_pos) if total_rev_pos > 0 else None

# ---- KPI cards ----
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Inc Revenue (Net, Selected Month)", f"{total_rev_net:,.0f}")
c2.metric("Total Positive Contributions", f"{total_rev_pos:,.0f}")
c3.metric("Total Negative Contributions", f"{total_rev_neg:,.0f}")  # will show negative number
c4.metric("Top Segment", top_seg)
c5.metric("Top Segment Inc Revenue", f"{top_rev:,.0f}")

# ---- Correct interpretation note ----
if share_of_net is not None and share_of_net > 1.0:
    st.info(
        "Note: Top segment revenue exceeds the NET total because other segments are negative in the same month. "
        "This is expected in segmented incrementality views."
    )

# ---- Concentration metric (recommended) ----
st.caption(
    "Concentration: share of Top Segment within POSITIVE contributions = "
    + (f"{share_of_positive*100:,.1f}%" if share_of_positive is not None else "N/A")
    + " (recommended)."
)

# ---- Auto narrative (uses net totals; OK) ----
n = narrative_rfm(
    top_seg=top_seg,
    top_rev=top_rev,
    total_rev=total_rev_net,
    bottom_seg=bottom_seg,
    bottom_rev=bottom_rev
)
render_narrative(n, expanded=True)

# ---- Chart 1: Selected month bar ----
st.subheader("Incremental Revenue by RFM Segment (Selected Month)")
title_month = m["month_label"].iloc[0] if len(m) else sel_month

fig1 = px.bar(
    m,
    x="rfm_segment",
    y="incremental_revenue",
    title=f"Incremental Revenue by RFM Segment ({title_month})"
)
fig1.update_xaxes(type="category", title="RFM Segment")
st.plotly_chart(fig1, use_container_width=True)

# ---- Optional: show positive vs negative split table ----
st.subheader("Positive vs Negative Contribution (Selected Month)")
m2 = m.copy()
m2["contribution_sign"] = m2["incremental_revenue"].apply(lambda x: "Positive" if x > 0 else ("Negative" if x < 0 else "Zero"))
st.dataframe(
    m2.sort_values(["contribution_sign", "incremental_revenue"], ascending=[True, False])
      [["rfm_segment", "contribution_sign", "incremental_revenue", "customers", "incremental_transactions", "avg_delta_aov"]]
)

# ---- Chart 2: Matrix Month × Segment ----
st.subheader("Matrix: Month × Segment (Incremental Revenue)")
rfm_agg = rfm.groupby(["rfm_segment", "month_label"], as_index=False).agg(
    incremental_revenue=("incremental_revenue", "sum")
)

matrix = rfm_agg.pivot_table(
    index="rfm_segment",
    columns="month_label",
    values="incremental_revenue",
    aggfunc="sum",
    fill_value=0.0
).reset_index()

st.dataframe(matrix)

# ---- Chart 3: Trend for overall Top 5 segments (across all months) ----
st.subheader("Trend: Overall Top 5 RFM Segments Over Time")
top5 = (
    rfm.groupby("rfm_segment", as_index=False)["incremental_revenue"].sum()
       .sort_values("incremental_revenue", ascending=False)
       .head(5)["rfm_segment"]
       .tolist()
)

rfm_top = rfm_agg[rfm_agg["rfm_segment"].isin(top5)].copy()

fig2 = px.line(
    rfm_top,
    x="month_label",
    y="incremental_revenue",
    color="rfm_segment",
    title="Incremental Revenue Trend (Overall Top 5 RFM Segments)"
)
fig2.update_xaxes(type="category", title="Month")
st.plotly_chart(fig2, use_container_width=True)

# ---- Detail table (selected month) ----
st.subheader("Detail Table (Selected Month)")
cols = ["rfm_segment", "customers", "incremental_revenue", "incremental_transactions", "avg_delta_aov"]
cols = [c for c in cols if c in m.columns]
st.dataframe(m[cols])

# ---- Download ----
st.subheader("Download data")
st.download_button(
    "Download agg_incrementality_rfm.csv",
    data=rfm.to_csv(index=False),
    file_name="agg_incrementality_rfm.csv"
)

# ---- Debug / audit ----
with st.expander("Debug / Data audit", expanded=False):
    st.write("Selected month_id_norm:", sel_month)
    st.write("Rows in raw rfm:", len(rfm))
    st.write("Rows in rfm_month:", len(rfm_month))
    st.write("Rows in m (aggregated):", len(m))
    st.write("Net total (selected month):", total_rev_net)
    st.write("Total positive contributions:", total_rev_pos)
    st.write("Total negative contributions:", total_rev_neg)
    st.write("Top segment / revenue:", top_seg, top_rev)
    st.dataframe(m.head(10))
