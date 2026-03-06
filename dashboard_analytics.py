import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Toy Story Product Analytics Dashboard",
    layout="wide"
)

st.title("Toy Story Product Analytics Dashboard")

file = st.file_uploader("Upload Sales Data", type=["xlsx","csv"])

if file:

    if file.name.endswith("xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)

    # ------------------------
    # METRIC SWITCH
    # ------------------------

    metric = st.radio(
        "Metric",
        ["Units Sold","Revenue"],
        horizontal=True
    )

    if metric == "Units Sold":
        value_col = "Quantity_Sold"
        label = "Units Sold"
    else:
        value_col = "Total_Sales_Baht"
        label = "Revenue"

    # ------------------------
    # FILTERS
    # ------------------------

    st.sidebar.header("Filters")

    channel = st.sidebar.multiselect(
        "Channel",
        sorted(df["sales_Channel"].unique()),
        default=sorted(df["sales_Channel"].unique())
    )

    fabric = st.sidebar.multiselect(
        "Fabric",
        sorted(df["Fabric"].unique()),
        default=sorted(df["Fabric"].unique())
    )

    search = st.sidebar.text_input("Search SKU")

    sku_list = sorted(df["Product_Code"].unique())

    if search:
        sku_list = [s for s in sku_list if search.lower() in s.lower()]

    sku = st.sidebar.multiselect(
        "Select SKU",
        sku_list,
        default=sku_list
    )

    df = df[
        (df["sales_Channel"].isin(channel)) &
        (df["Fabric"].isin(fabric)) &
        (df["Product_Code"].isin(sku))
    ]

    # ------------------------
    # KPI
    # ------------------------

    total_value = df[value_col].sum()
    total_units = df["Quantity_Sold"].sum()
    sku_count = df["Product_Code"].nunique()

    k1,k2,k3 = st.columns(3)

    k1.metric(label, f"{total_value:,.0f}")
    k2.metric("Total Units", f"{total_units:,.0f}")
    k3.metric("Active SKU", sku_count)

    st.divider()

    # ------------------------
    # EXECUTIVE SUMMARY
    # ------------------------

    st.subheader("Executive Summary")

    top_sku = df.groupby("Product_Code")["Quantity_Sold"].sum().idxmax()
    top_units = df.groupby("Product_Code")["Quantity_Sold"].sum().max()

    top_channel = df.groupby("sales_Channel")["Quantity_Sold"].sum().idxmax()

    slow_sku = df.groupby("Product_Code")["Quantity_Sold"].sum().idxmin()

    st.markdown(f"""
**Key Insights**

• ⭐ Top SKU: **{top_sku}** with **{top_units:,} units sold**

• 🛒 Strongest Channel: **{top_channel}**

• 🔁 Reprint Priority: **{top_sku}**

• 💤 Slow Moving SKU: **{slow_sku}**
""")

    # ------------------------
    # AI BUSINESS INSIGHTS
    # ------------------------

    st.subheader("AI Business Insights")

    channel_share = (
        df.groupby("sales_Channel")["Quantity_Sold"]
        .sum()
        .sort_values(ascending=False)
    )

    top_channel_pct = channel_share.iloc[0] / channel_share.sum()

    top3_share = (
        df.groupby("Product_Code")["Quantity_Sold"]
        .sum()
        .sort_values(ascending=False)
        .head(3)
        .sum()
        / df["Quantity_Sold"].sum()
    )

    ai_insights = []

    if top_channel_pct > 0.5:
        ai_insights.append(
            f"⚠ Demand is highly concentrated in **{channel_share.index[0]}** ({top_channel_pct:.0%}). Consider diversifying channels."
        )

    if top3_share > 0.6:
        ai_insights.append(
            f"📦 Top 3 SKUs generate **{top3_share:.0%}** of total demand. Inventory planning should prioritize these."
        )

    slow_share = (
        df.groupby("Product_Code")["Quantity_Sold"]
        .sum()
        .sort_values()
        .head(5)
        .sum()
        / df["Quantity_Sold"].sum()
    )

    if slow_share < 0.1:
        ai_insights.append(
            "💤 Bottom SKUs contribute very little demand. Consider discontinuing or bundling slow movers."
        )

    for insight in ai_insights:
        st.markdown(f"- {insight}")

    # ------------------------
    # CHANNEL PERFORMANCE
    # ------------------------

    channel_sales = (
        df.groupby("sales_Channel")[value_col]
        .sum()
        .reset_index()
    )

    fig_channel = px.bar(
        channel_sales,
        x="sales_Channel",
        y=value_col,
        color="sales_Channel",
        title=f"{label} by Channel",
        template="plotly_dark"
    )

    st.plotly_chart(fig_channel,use_container_width=True)

    # ------------------------
    # CHANNEL SHARE
    # ------------------------

    fig_share = px.pie(
        channel_sales,
        names="sales_Channel",
        values=value_col,
        title="Channel Share",
        template="plotly_dark"
    )

    st.plotly_chart(fig_share,use_container_width=True)

    # ------------------------
    # TOP SKU
    # ------------------------

    top_products = (
        df.groupby("Product_Code")[value_col]
        .sum()
        .reset_index()
        .sort_values(value_col,ascending=False)
        .head(15)
    )

    fig_top = px.bar(
        top_products,
        x="Product_Code",
        y=value_col,
        color=value_col,
        title="Top SKU",
        template="plotly_dark"
    )

    st.plotly_chart(fig_top,use_container_width=True)

    # ------------------------
    # HEATMAP
    # ------------------------

    heat = pd.pivot_table(
        df,
        values=value_col,
        index="Product_Code",
        columns="sales_Channel",
        aggfunc="sum",
        fill_value=0
    )

    fig_heat = px.imshow(
        heat,
        color_continuous_scale="Blues",
        aspect="auto",
        labels={"color":label},
        title="SKU vs Channel Heatmap"
    )

    fig_heat.update_layout(height=550)

    st.plotly_chart(fig_heat,use_container_width=True)

    # ------------------------
    # SKU CHANNEL DEPENDENCY
    # ------------------------

    dep = (
        df.groupby(["Product_Code","sales_Channel"])["Quantity_Sold"]
        .sum()
        .reset_index()
    )

    fig_dep = px.bar(
        dep,
        x="Product_Code",
        y="Quantity_Sold",
        color="sales_Channel",
        title="SKU Channel Dependency"
    )

    st.plotly_chart(fig_dep,use_container_width=True)

    # ------------------------
    # SKU CONCENTRATION
    # ------------------------

    pareto = (
        df.groupby("Product_Code")[value_col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    pareto["cum"] = pareto[value_col].cumsum()
    pareto["pct"] = pareto["cum"]/pareto[value_col].sum()

    fig_pareto = px.line(
        pareto,
        x="Product_Code",
        y="pct",
        markers=True,
        title="SKU Concentration (Pareto)"
    )

    st.plotly_chart(fig_pareto,use_container_width=True)

    # ------------------------
    # REPRINT
    # ------------------------

    st.subheader("Reprint Candidates")

    reprint = (
        df.groupby("Product_Code")["Quantity_Sold"]
        .sum()
        .reset_index()
        .sort_values("Quantity_Sold",ascending=False)
        .head(10)
    )

    st.dataframe(reprint,hide_index=True)

    st.download_button(
        "Download Reprint List",
        reprint.to_csv(index=False),
        "reprint_candidates.csv"
    )

    # ------------------------
    # SLOW MOVERS
    # ------------------------

    st.subheader("Slow Moving SKU")

    slow = (
        df.groupby("Product_Code")["Quantity_Sold"]
        .sum()
        .reset_index()
        .sort_values("Quantity_Sold")
        .head(10)
    )

    st.dataframe(slow,hide_index=True)