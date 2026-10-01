"""Streamlit dashboard for the PharmEasy Regional Pulse project."""
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from metrics_engine import flag_significant_regions_v1

DB_FILE = Path("pharmeasy.db")

st.set_page_config(page_title="PharmEasy Regional Pulse", layout="wide")


@st.cache_data
def load_data():
    with sqlite3.connect(DB_FILE) as conn:
        orders = pd.read_sql_query("SELECT * FROM orders_clean", conn)
        monthly = pd.read_sql_query(
            """
            SELECT region, substr(order_date, 1, 7) AS month,
                   ROUND(SUM(sales_inr), 2) AS sales_inr,
                   ROUND(SUM(profit_inr), 2) AS profit_inr,
                   COUNT(DISTINCT order_id) AS order_count
            FROM orders_clean
            GROUP BY region, substr(order_date, 1, 7)
            ORDER BY region, month
            """,
            conn,
        )
    return orders, monthly


orders, monthly = load_data()

st.title("PharmEasy Regional Pulse")
st.caption("A local, SQL-backed view of regional order performance for April–June 2026.")

# Executive summary uses the actual clean dataset rather than hard-coded dashboard KPIs.
total_sales = orders["sales_inr"].sum()
total_profit = orders["profit_inr"].sum()
total_orders = orders["order_id"].nunique()
guntur = monthly[monthly["region"] == "Guntur"].set_index("month")
guntur_change = (guntur.loc["2026-05", "sales_inr"] - guntur.loc["2026-04", "sales_inr"]) / guntur.loc["2026-04", "sales_inr"] * 100
may_category = (
    orders[(orders["region"] == "Guntur") & (orders["order_date"].str.startswith("2026-05"))]
    .groupby("category", as_index=False)["sales_inr"].sum()
    .sort_values("sales_inr", ascending=False)
)
category_leader = may_category.iloc[0]

st.info(
    f"Total cleaned sales are ₹{total_sales:,.2f} from {total_orders:,} distinct orders, "
    f"with total profit of ₹{total_profit:,.2f}. Guntur's sales rose {guntur_change:.2f}% from April to May, "
    f"then moved to ₹{guntur.loc['2026-06', 'sales_inr']:,.2f} in June. In May, {category_leader['category']} "
    f"was Guntur's largest category at ₹{category_leader['sales_inr']:,.2f}. Use the charts and detail table below "
    "to inspect the same numbers by region and month."
)


# CII narrative: the dashboard repeats the same alert rule used by the metrics layer.
change_rows = monthly.pivot(index="region", columns="month", values="sales_inr").fillna(0)
april_may_changes = ((change_rows["2026-05"] - change_rows["2026-04"]) / change_rows["2026-04"] * 100).to_dict()
may_june_changes = ((change_rows["2026-06"] - change_rows["2026-05"]) / change_rows["2026-05"] * 100).to_dict()
flagged = sorted(set(flag_significant_regions_v1(april_may_changes)) | set(flag_significant_regions_v1(may_june_changes)))

with st.expander("CII narrative — what do the flagged movements mean?", expanded=False):
    for region in flagged:
        region_rows = monthly[monthly["region"] == region].set_index("month")
        changes = []
        if region in april_may_changes and abs(april_may_changes[region]) > 8:
            changes.append(f"April→May: {april_may_changes[region]:.2f}%")
        if region in may_june_changes and abs(may_june_changes[region]) > 8:
            changes.append(f"May→June: {may_june_changes[region]:.2f}%")
        st.markdown(f"**{region}** — **Context:** monthly sales are ₹{region_rows.loc['2026-04', 'sales_inr']:,.2f} in April, ₹{region_rows.loc['2026-05', 'sales_inr']:,.2f} in May and ₹{region_rows.loc['2026-06', 'sales_inr']:,.2f} in June.  \n**Insight:** {'; '.join(changes)}.  \n**Implication:** this is a review alert, not proof of a cause; check the underlying order/category mix before acting.")


k1, k2, k3 = st.columns(3)
k1.metric("Total sales", f"₹{total_sales:,.0f}")
k2.metric("Total profit", f"₹{total_profit:,.0f}")
k3.metric("Distinct orders", f"{total_orders:,}")

regions = ["All regions"] + sorted(orders["region"].unique().tolist())
selected_region = st.selectbox("Region", regions)
months = sorted(orders["order_date"].str[:7].unique())
selected_month = st.selectbox("Month for category view", months, index=len(months) - 1)

filtered_orders = orders if selected_region == "All regions" else orders[orders["region"] == selected_region]

st.subheader("Overview — how are sales moving over time?")
line_data = monthly if selected_region == "All regions" else monthly[monthly["region"] == selected_region]
fig_line = px.line(
    line_data,
    x="month",
    y="sales_inr",
    color="region",
    markers=True,
    title="How do monthly sales move across regions?",
    labels={"month": "Month", "sales_inr": "Sales (INR)", "region": "Region"},
)
fig_line.update_yaxes(rangemode="tozero")
st.plotly_chart(fig_line, use_container_width=True)

st.subheader("Region comparison — which regions contribute the most sales?")
bar_data = (
    monthly.groupby("region", as_index=False)["sales_inr"].sum().sort_values("sales_inr", ascending=False)
)
if selected_region != "All regions":
    bar_data = bar_data[bar_data["region"] == selected_region]
fig_bar = px.bar(
    bar_data,
    x="region",
    y="sales_inr",
    title="Which regions have the highest total sales across April–June?",
    labels={"region": "Region", "sales_inr": "Sales (INR)"},
)
fig_bar.update_yaxes(rangemode="tozero")
st.plotly_chart(fig_bar, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Category — what drove the selected month?")
    category_data = (
        filtered_orders[filtered_orders["order_date"].str.startswith(selected_month)]
        .groupby("category", as_index=False)["sales_inr"].sum()
        .sort_values("sales_inr", ascending=False)
    )
    fig_pie = px.pie(
        category_data,
        names="category",
        values="sales_inr",
        hole=0.45,
        title=f"What is the sales share by category in {selected_month}?",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with right:
    st.subheader("Detail — what does the region/month table show?")
    detail = monthly if selected_region == "All regions" else monthly[monthly["region"] == selected_region]
    detail = detail.sort_values(["month", "region"])
    st.dataframe(detail, use_container_width=True, hide_index=True)

st.caption("The 8% movement rule is an operational review alert; it does not establish a cause by itself.")
