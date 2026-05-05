import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title = "Afficionado Coffee Roasters", page_icon = "☕", layout = "wide")

@st.cache_data
def load_data():
    data = pd.read_csv("data/afficionado_cleaned.csv")
    pareto = pd.read_csv("data/pareto_data.csv")
    return data, pareto

data, pareto = load_data()

st.title("Afficionado Coffee Roasters")
st.subheader("Product Optimization & Revenue Contribution Analysis")
st.divider()

st.sidebar.image("Logo_bg_removed.png", width = 250)

st.sidebar.header("Filters")
categories = ["All"] + sorted(data["product_category"].unique().tolist())
selected_category = st.sidebar.selectbox("Product Category", categories)
if selected_category == "All":
    types = ["All"] + sorted(data["product_type"].unique().tolist())
else:
    types = ["All"] + sorted(data[data["product_category"] == selected_category]["product_type"].unique().tolist())
selected_type = st.sidebar.selectbox("Product Type", types)
locations = ["All"] + sorted(data["store_location"].unique().tolist())
selected_location = st.sidebar.selectbox("Store Location", locations)
top_n = st.sidebar.slider("Top N Products", min_value = 1, max_value = 20, value = 10)

filtered_data = data.copy()
if selected_category != "All":
    filtered_data = filtered_data[filtered_data["product_category"] == selected_category]
if selected_type != "All":
    filtered_data = filtered_data[filtered_data["product_type"] == selected_type]
if selected_location != "All":
    filtered_data = filtered_data[filtered_data["store_location"] == selected_location]

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Product Performance", "Category Analysis", "Revenue Concentration", "Product Drill Down"])

with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${filtered_data["revenue"].sum():.2f}")
    col2.metric("Total Units Sold", f"${filtered_data["transaction_qty"].sum():,}")
    col3.metric("Total Transactions", f"{filtered_data["transaction_id"].nunique():,}")
    col4.metric("Unique Products", f"{filtered_data["product_id"].nunique():,}")

    category_revenue = filtered_data.groupby("product_category")["revenue"].sum().reset_index()
    fig_donut = px.pie(category_revenue, names = "product_category", values = "revenue", hole = 0.4, title = "Revenue by Category")
    st.plotly_chart(fig_donut)
    
    store_revenue = filtered_data.groupby("store_location")["revenue"].sum().reset_index()
    store_revenue = store_revenue.sort_values("revenue", ascending = True)
    fig_store = px.bar(store_revenue, x = "revenue", y = "store_location", orientation = "h", title = "Revenue by Store Location")
    st.plotly_chart(fig_store)

with tab2:
    product_stats = filtered_data.groupby("product_detail").agg(total_revenue = ("revenue", "sum"), total_units = ("transaction_qty", "sum")).reset_index()
    product_stats = product_stats.sort_values("total_revenue", ascending = False)
    top_products = product_stats.head(top_n)

    fig_rev = px.bar(top_products.sort_values("total_revenue", ascending = True), x = "total_revenue", y = "product_detail", orientation = "h", title = f"Top {top_n} Products by Revenue")
    st.plotly_chart(fig_rev)
    
    top_units = product_stats.sort_values("total_units", ascending = False).head(top_n)
    fig_units = px.bar(top_units.sort_values("total_units", ascending = True), x = "total_units", y = "product_detail", orientation = "h", title = f"Top {top_n} Products by Units Sold")
    st.plotly_chart(fig_units)

    fig_cluster = go.Figure()
    fig_cluster.add_trace(go.Bar(name = "Revenue", x = top_products["product_detail"], y = top_products["total_revenue"]))
    fig_cluster.add_trace(go.Bar(name = "Units Sold", x = top_products["product_detail"], y = top_products["total_units"]))
    fig_cluster.update_layout(barmode = "group", title = f"Revenue vs Units Sold - {top_n} Products")
    st.plotly_chart(fig_cluster)

with tab3:
    type_revenue = filtered_data.groupby(["product_category", "product_type"])["revenue"].sum().reset_index()
    fig_stacked = px.bar(type_revenue, x = "product_category", y = "revenue", color = "product_type", title = "Revenue by Category and Product Type", barmode = "stack")
    st.plotly_chart(fig_stacked)

    matrix = filtered_data.groupby(["product_category", "product_type"]).agg(total_revenue = ("revenue", sum), total_units = ("transaction_qty", "sum")).reset_index()
    matrix["revenue_share_%"] = (matrix["total_revenue"]/matrix["total_revenue"].sum())
    matrix = matrix.sort_values("total_revenue", ascending = False)
    st.subheader("Revenue Performance by Category & Type")
    st.dataframe(matrix)

    product_share = filtered_data.groupby("product_detail")["revenue"].sum().reset_index()
    product_share["revenue_share_%"] = (product_share["revenue"]/product_share["revenue"].sum()*100).round(2)
    product_share = product_share.sort_values("revenue_share_%", ascending = True).tail(top_n)
    fig_share = px.bar(product_share, x = "revenue_share_%", y = "product_detail", orientation = "h", title = f"Revenue Contribution % - Top {top_n} Products")
    st.plotly_chart(fig_share)

with tab4:
    heroes = pareto[pareto["Cumulative PCT"] <= 80]
    st.metric("Products Driving 80% of Revenue", len(heroes))
    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(x = pareto["Rank"], y = pareto["revenue"], name = "Revenue", marker_color = "darkgreen"))
    fig_pareto.add_trace(go.Scatter(x = pareto["Rank"], y = pareto["Cumulative PCT"], name = "Cumulative %", yaxis = "y2", line = dict(color = "red", width = 2)))
    fig_pareto.update_layout(title = "Revenue Concentration by Product Rank", yaxis2 = dict(overlaying = "y", side = "right", range = [0, 100]), shapes = [dict(type = "line", x0 = 0, x1 = pareto["Rank"].max(), y0 = 80, y1 = 80, yref = "y2", line = dict(color = "orange", dash = "dash", width = 2))])
    st.plotly_chart(fig_pareto)

    st.subheader("Hero Products (Driving 80% Revenue)")
    st.dataframe(heroes[["Rank", "product_detail", "revenue", "Cumulative PCT"]])
    
    long_tail = pareto[pareto["Cumulative PCT"] > 80]
    st.subheader("Long Tail Products")
    st.dataframe(long_tail[["Rank", "product_detail", "revenue", "Cumulative PCT"]])

with tab5:
    drill = filtered_data.groupby(["product_detail", "product_category", "product_type"]).agg(total_revenue = ("revenue", "sum"), total_units = ("transaction_qty", "sum")).reset_index()
    drill["revenue_share_%"] = (drill["total_revenue"]/drill["total_revenue"].sum()*100).round(2)
    drill["rank"] = drill["total_revenue"].rank(ascending = False).astype(int)
    drill = drill.sort_values("rank")

    st.subheader("Product Drill-Down Table")
    st.dataframe(drill)

