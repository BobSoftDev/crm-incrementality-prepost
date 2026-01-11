import streamlit as st
import plotly.express as px

from utils.data import (
    get_default_export_folder,
    load_csv_folder,
    ensure_month_fields,
    sort_month
)
from utils.narrative import render_narrative, narrative_diagnostics

st.title("Diagnostics (Analyst Only)")

folder = st.sidebar.text_input("Gold export folder", value=get_default_export_folder())

fact = load_csv_folder(folder, "fact_customer_month_incrementality.csv")
fact = ensure_month_fields(fact, "month_id")
fact = sort_month(fact)

months = [m for m in fact["month_id_norm"].unique().tolist() if m != "Unknown"]
months = sorted(months)
sel_month = st.selectbox("Select month", months, index=(len(months)-1) if len(months) else 0)

m = fact[fact["month_id_norm"] == sel_month].copy()

st.subheader("Coverage & Sanity Checks")

rows = len(m)
customers = m["customer_id"].nunique() if "customer_id" in m.columns else 0
zero_pre = int((m["pre_revenue"] == 0).sum()) if "pre_revenue" in m.columns else 0
zero_post = int((m["post_revenue"] == 0).sum()) if "post_revenue" in m.columns else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows (customer-month)", f"{rows:,}")
c2.metric("Unique customers", f"{customers:,}")
c3.metric("Zero PRE revenue rows", f"{zero_pre:,}")
c4.metric("Zero POST revenue rows", f"{zero_post:,}")

inc_rev_median = float(m["incremental_revenue"].median()) if ("incremental_revenue" in m.columns and len(m)) else None

# Auto narrative
n = narrative_diagnostics(
    rows=rows,
    customers=customers,
    zero_pre=zero_pre,
    zero_post=zero_post,
    inc_rev_median=inc_rev_median
)
render_narrative(n, expanded=True)

st.subheader("Distribution: Incremental Revenue")
if "incremental_revenue" in m.columns and len(m):
    fig1 = px.histogram(m, x="incremental_revenue", nbins=60, title="Incremental Revenue Distribution")
    st.plotly_chart(fig1, use_container_width=True)

st.subheader("PRE vs POST Revenue per Day (Box proxy)")
needed = ["pre_rev_per_day", "post_rev_per_day"]
if all(c in m.columns for c in needed) and len(m):
    df_melt = m[needed].copy()
    df_melt["row_id"] = range(len(df_melt))
    df_melt = df_melt.melt(id_vars=["row_id"], var_name="period", value_name="rev_per_day")
    fig2 = px.box(df_melt, x="period", y="rev_per_day", points="all", title="PRE vs POST Revenue per Day (Box)")
    fig2.update_xaxes(type="category")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Top Outliers (Selected Month)")
if "incremental_revenue" in m.columns and "customer_id" in m.columns and len(m):
    top_pos = m.sort_values("incremental_revenue", ascending=False).head(20)
    top_neg = m.sort_values("incremental_revenue", ascending=True).head(20)

    st.write("Top 20 positive incremental revenue rows")
    st.dataframe(top_pos[["customer_id", "month_label", "incremental_revenue", "pre_revenue", "post_revenue"]])

    st.write("Top 20 negative incremental revenue rows")
    st.dataframe(top_neg[["customer_id", "month_label", "incremental_revenue", "pre_revenue", "post_revenue"]])

st.subheader("Download data")
st.download_button(
    "Download fact_customer_month_incrementality.csv",
    data=fact.to_csv(index=False),
    file_name="fact_customer_month_incrementality.csv"
)
