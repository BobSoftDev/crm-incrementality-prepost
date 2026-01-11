import streamlit as st
import plotly.express as px

from utils.data import (
    get_default_export_folder,
    load_csv_folder,
    ensure_month_fields,
    sort_month
)
from utils.narrative import render_narrative, narrative_value_split

st.title("Incrementality by Customer Value")

folder = st.sidebar.text_input("Gold export folder", value=get_default_export_folder())

df = load_csv_folder(folder, "agg_incrementality_active_value.csv")
df = ensure_month_fields(df, "month_id")
df = sort_month(df)

# Normalize flags
df["is_active"] = df["is_active"].astype(int)
df["is_high_value"] = df["is_high_value"].astype(int)

months = [m for m in df["month_id_norm"].unique().tolist() if m != "Unknown"]
months = sorted(months)
sel_month = st.selectbox("Select month", months, index=len(months)-1 if len(months) else 0)

m = df[df["month_id_norm"] == sel_month].copy()
m["value_group"] = m["is_high_value"].map({0: "Low Value", 1: "High Value"})
m["active_group"] = m["is_active"].map({0: "Non-Active", 1: "Active"})

# KPIs
total_inc_rev = float(m["incremental_revenue"].sum()) if len(m) else 0.0
hv_inc_rev = float(m[m["is_high_value"] == 1]["incremental_revenue"].sum()) if len(m) else 0.0
lv_inc_rev = float(m[m["is_high_value"] == 0]["incremental_revenue"].sum()) if len(m) else 0.0

c1, c2, c3 = st.columns(3)
c1.metric("Incremental Revenue (All)", f"{total_inc_rev:,.0f}")
c2.metric("Incremental Revenue (High Value)", f"{hv_inc_rev:,.0f}")
c3.metric("Incremental Revenue (Low Value)", f"{lv_inc_rev:,.0f}")

# Auto narrative
n = narrative_value_split(
    inc_all=total_inc_rev,
    inc_hv=hv_inc_rev,
    inc_lv=lv_inc_rev,
    hv_label="High Value",
    lv_label="Low Value"
)
render_narrative(n, expanded=True)

st.subheader("Incremental Revenue by Customer Value (Selected Month)")
v = m.groupby("value_group", as_index=False)["incremental_revenue"].sum()

fig1 = px.bar(
    v,
    x="value_group",
    y="incremental_revenue",
    title="Incremental Revenue by Customer Value"
)
fig1.update_xaxes(type="category", title="Value Group")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Incremental Revenue Split: Active vs Value (Selected Month)")
pivot = m.groupby(["active_group", "value_group"], as_index=False).agg(
    incremental_revenue=("incremental_revenue", "sum"),
    incremental_transactions=("incremental_transactions", "sum"),
    avg_delta_aov=("avg_delta_aov", "mean"),
    customers=("customers", "sum")
)

fig2 = px.bar(
    pivot,
    x="active_group",
    y="incremental_revenue",
    color="value_group",
    barmode="group",
    title="Incremental Revenue Split: Active vs Value"
)
fig2.update_xaxes(type="category", title="Active Group")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Detail Table")
st.dataframe(pivot.sort_values(["active_group", "value_group"]))

st.subheader("Download data")
st.download_button(
    "Download agg_incrementality_active_value.csv",
    data=df.to_csv(index=False),
    file_name="agg_incrementality_active_value.csv"
)
