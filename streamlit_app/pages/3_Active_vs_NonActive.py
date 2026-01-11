import streamlit as st
import plotly.express as px
import pandas as pd

from utils.data import (
    get_default_export_folder,
    load_csv_folder,
    ensure_month_fields,
    sort_month
)
from utils.narrative import render_narrative, narrative_active_vs_nonactive

st.title("Active vs Non-Active")

folder = st.sidebar.text_input("Gold export folder", value=get_default_export_folder())

# IMPORTANT: required=False so the page does not crash on missing file
df = load_csv_folder(folder, "agg_incrementality_active_value.csv", required=False)

if df.empty:
    st.error(
        "Missing data file: agg_incrementality_active_value.csv\n\n"
        "To fix:\n"
        "- Export Gold CSVs into 'data/gold_exports/' (recommended for Streamlit Cloud), or\n"
        "- Set the sidebar 'Gold export folder' to the folder that contains the CSV."
    )
    st.stop()

# Ensure numeric types safely
for col in ["incremental_revenue", "incremental_transactions", "avg_delta_aov", "customers", "is_active"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

df = ensure_month_fields(df, "month_id")
df = sort_month(df)

# Ensure is_active is int-like
if "is_active" in df.columns:
    df["is_active"] = df["is_active"].astype(int)
else:
    st.error("Column 'is_active' not found in agg_incrementality_active_value.csv")
    st.stop()

# Aggregate across value dimension to focus on Active vs Non-Active
by_month_active = df.groupby(["month_id_norm", "month_label", "is_active"], as_index=False).agg(
    customers=("customers", "sum"),
    incremental_revenue=("incremental_revenue", "sum"),
    incremental_transactions=("incremental_transactions", "sum"),
    avg_delta_aov=("avg_delta_aov", "mean")
)
by_month_active["active_group"] = by_month_active["is_active"].map({0: "Non-Active", 1: "Active"})

months = [m for m in by_month_active["month_id_norm"].unique().tolist() if m != "Unknown"]
months = sorted(months)

if not months:
    st.error("No valid months found in data. Check 'month_id' values in the CSV.")
    st.stop()

sel_month = st.selectbox("Select month", months, index=len(months) - 1)

m = by_month_active[by_month_active["month_id_norm"] == sel_month].copy()

# KPI cards
active_txn = float(m.loc[m["is_active"] == 1, "incremental_transactions"].sum()) if len(m) else 0.0
nonactive_txn = float(m.loc[m["is_active"] == 0, "incremental_transactions"].sum()) if len(m) else 0.0
active_rev = float(m.loc[m["is_active"] == 1, "incremental_revenue"].sum()) if len(m) else 0.0
nonactive_rev = float(m.loc[m["is_active"] == 0, "incremental_revenue"].sum()) if len(m) else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Inc Txns (Active)", f"{active_txn:,.0f}")
c2.metric("Inc Txns (Non-Active)", f"{nonactive_txn:,.0f}")
c3.metric("Inc Revenue (Active)", f"{active_rev:,.0f}")
c4.metric("Inc Revenue (Non-Active)", f"{nonactive_rev:,.0f}")

# Auto narrative
n = narrative_active_vs_nonactive(
    active_rev=active_rev,
    nonactive_rev=nonactive_rev,
    active_txn=active_txn,
    nonactive_txn=nonactive_txn
)
render_narrative(n, expanded=True)

st.subheader("Incremental Transactions by Active Group (Selected Month)")
fig1 = px.bar(
    m,
    x="active_group",
    y="incremental_transactions",
    title="Incremental Transactions: Active vs Non-Active"
)
fig1.update_xaxes(type="category", title="Active Group")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Trend: Incremental Revenue Over Time by Active Group")
fig2 = px.line(
    by_month_active,
    x="month_label",
    y="incremental_revenue",
    color="active_group",
    title="Incremental Revenue Trend by Active Group"
)
fig2.update_xaxes(type="category", title="Month")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Trend: Incremental Transactions Over Time by Active Group")
fig3 = px.line(
    by_month_active,
    x="month_label",
    y="incremental_transactions",
    color="active_group",
    title="Incremental Transactions Trend by Active Group"
)
fig3.update_xaxes(type="category", title="Month")
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Detail Table")
st.dataframe(by_month_active.sort_values(["month_id_norm", "is_active"]))

st.subheader("Download data")
st.download_button(
    "Download agg_incrementality_active_value.csv",
    data=df.to_csv(index=False),
    file_name="agg_incrementality_active_value.csv"
)

with st.expander("Debug / Data audit", expanded=False):
    st.write("Folder input:", folder)
    st.write("Default export folder:", get_default_export_folder())
    st.write("Rows in df:", len(df))
    st.write("Rows in by_month_active:", len(by_month_active))
    st.dataframe(by_month_active.head(10))
