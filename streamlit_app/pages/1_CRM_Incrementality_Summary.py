import streamlit as st
import plotly.express as px

from utils.data import (
    get_default_export_folder,
    load_csv_folder,
    ensure_month_fields,
    sort_month
)
from utils.narrative import render_narrative, narrative_summary

st.title("CRM Incrementality Summary")

folder = st.sidebar.text_input("Gold export folder", value=get_default_export_folder())

agg_month = load_csv_folder(folder, "agg_incrementality_month.csv")
agg_rfm = load_csv_folder(folder, "agg_incrementality_rfm.csv")

agg_month = ensure_month_fields(agg_month, "month_id")
agg_rfm = ensure_month_fields(agg_rfm, "month_id")

agg_month = sort_month(agg_month)
agg_rfm = sort_month(agg_rfm)

# KPIs
total_inc_rev = float(agg_month["incremental_revenue"].sum()) if len(agg_month) else 0.0
total_inc_txn = float(agg_month["incremental_transactions"].sum()) if len(agg_month) else 0.0
avg_delta_aov = float(agg_month["avg_delta_aov"].mean()) if len(agg_month) else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Incremental Revenue", f"{total_inc_rev:,.0f}")
c2.metric("Incremental Transactions", f"{total_inc_txn:,.0f}")
c3.metric("Avg ΔAOV", f"{avg_delta_aov:,.2f}")

# Trend
fig = px.line(
    agg_month,
    x="month_label",
    y="incremental_revenue",
    title="Incremental Revenue by Month"
)
fig.update_xaxes(type="category", title="Month")
st.plotly_chart(fig, use_container_width=True)

# Segment bar (selected month)
months = [m for m in agg_rfm["month_id_norm"].unique().tolist() if m != "Unknown"]
months = sorted(months)
sel_month = st.selectbox("Select month", months, index=len(months)-1 if len(months) else 0)

rfm_m = agg_rfm[agg_rfm["month_id_norm"] == sel_month].copy()
rfm_m = rfm_m.fillna({"rfm_segment": "Unknown"}).sort_values("incremental_revenue", ascending=False)

fig2 = px.bar(
    rfm_m,
    x="rfm_segment",
    y="incremental_revenue",
    title=f"Incremental Revenue by RFM Segment ({rfm_m['month_label'].iloc[0] if len(rfm_m) else sel_month})"
)
fig2.update_xaxes(type="category", title="RFM Segment")
st.plotly_chart(fig2, use_container_width=True)

top_seg = str(rfm_m.iloc[0]["rfm_segment"]) if len(rfm_m) else "N/A"

# Auto narrative
n = narrative_summary(
    total_inc_rev=total_inc_rev,
    total_inc_txn=total_inc_txn,
    avg_delta_aov=avg_delta_aov,
    top_segment=top_seg
)
render_narrative(n, expanded=True)

# Downloads
st.subheader("Download data")
st.download_button(
    "Download agg_incrementality_month.csv",
    data=agg_month.to_csv(index=False),
    file_name="agg_incrementality_month.csv"
)
st.download_button(
    "Download agg_incrementality_rfm.csv",
    data=agg_rfm.to_csv(index=False),
    file_name="agg_incrementality_rfm.csv"
)
