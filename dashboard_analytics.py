import streamlit as st
import pandas as pd
import plotly.express as px

def fix_drive(url):

    if url is None:
        return ""

    url = str(url)

    if "drive.google.com/thumbnail" in url:
        file_id = url.split("id=")[1].split("&")[0]
        return f"https://drive.google.com/uc?id={file_id}"

    if "/file/d/" in url:
        file_id = url.split("/d/")[1].split("/")[0]
        return f"https://drive.google.com/uc?id={file_id}"

    return url

st.set_page_config(
    page_title="Product Analytics Dashboard",
    layout="wide"
)

st.title("Product Analytics Dashboard")

# -------------------------
# LOAD DATA
# -------------------------

uploaded_file = st.file_uploader(
    "Upload new Excel file (optional)",
    type=["xlsx"]
)

if uploaded_file:
    df = pd.read_excel(uploaded_file)
else:
    df = pd.read_excel("ToyStory-2025-ChatGPT.xlsx")

if "product_image_url" not in df.columns:
    df["product_image_url"] = ""

# -------------------------
# FIX GOOGLE DRIVE IMAGE
# -------------------------

def fix_drive(url):

    if pd.isna(url):
        return ""

    url = str(url)

    if "drive.google.com" in url:

        try:
            file_id = url.split("/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?id={file_id}"
        except:
            return ""

    return url

df["product_image_url"] = df["product_image_url"].apply(fix_drive)

# -------------------------
# METRIC SWITCH
# -------------------------

metric = st.radio(
    "Metric",
    ["Units Sold", "Revenue"],
    horizontal=True
)

if metric == "Units Sold":
    value_col = "Quantity_Sold"
    label = "Units Sold"
else:
    value_col = "Total_Sales_Baht"
    label = "Revenue"

# -------------------------
# SIDEBAR FILTER
# -------------------------

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

# -------------------------
# KPI
# -------------------------

total_value = df[value_col].sum()
total_units = df["Quantity_Sold"].sum()
sku_count = df["Product_Code"].nunique()

k1, k2, k3 = st.columns(3)

k1.metric(label, f"{total_value:,.0f}")
k2.metric("Total Units", f"{total_units:,.0f}")
k3.metric("Active SKU", sku_count)

st.divider()

# -------------------------
# EXECUTIVE SUMMARY
# -------------------------

st.subheader("Executive Summary")

top_sku = df.groupby("Product_Code")["Quantity_Sold"].sum().idxmax()
top_units = df.groupby("Product_Code")["Quantity_Sold"].sum().max()

top_channel = df.groupby("sales_Channel")["Quantity_Sold"].sum().idxmax()

slow_sku = df.groupby("Product_Code")["Quantity_Sold"].sum().idxmin()

st.markdown(f"""
⭐ **Top SKU:** {top_sku} ({top_units:,} units)

🛒 **Best Channel:** {top_channel}

💤 **Slowest SKU:** {slow_sku}
""")

# -------------------------
# PRODUCT GALLERY
# -------------------------

st.subheader("Product Gallery")

gallery_mode = st.radio(
    "Gallery Mode",
    ["Highlight Only", "Show All"],
    horizontal=True
)

gallery = (
    df.groupby(["Product_Code", "product_image_url"])["Quantity_Sold"]
    .sum()
    .reset_index()
    .sort_values("Quantity_Sold", ascending=False)
)

highlight = gallery.head(4)
rest = gallery.tail(len(gallery)-4)

st.markdown("### ⭐ Top Products")

cols = st.columns(4)

for i, (_, row) in enumerate(highlight.iterrows()):

    with cols[i]:

        if row["product_image_url"]:
            st.image(row["product_image_url"], use_container_width=True)
        else:
            st.markdown("### No Pic")

        st.markdown(f"**{row['Product_Code']}**")
        st.markdown(f"Units Sold: {row['Quantity_Sold']:,}")

if gallery_mode == "Show All":

    st.markdown("---")
    st.markdown("### All Products")

    per_row = 4
    idx = 0

    for r in range(len(rest)//4 + 1):

        cols = st.columns(per_row)

        for c in range(per_row):

            if idx >= len(rest):
                break

            row = rest.iloc[idx]

            with cols[c]:

                if row["product_image_url"]:
                    st.image(row["product_image_url"], use_container_width=True)
                else:
                    st.markdown("### No Pic")

                st.markdown(f"**{row['Product_Code']}**")
                st.markdown(f"Units Sold: {row['Quantity_Sold']:,}")

            idx += 1

# -------------------------
# PRODUCT EXPLORER
# -------------------------

st.divider()
st.subheader("Product Explorer")

selected_product = st.selectbox(
    "Select Product",
    sorted(df["Product_Code"].unique())
)

product_df = df[df["Product_Code"] == selected_product]

col1, col2 = st.columns([1,2])

image_url = product_df["product_image_url"].iloc[0]

with col1:

    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.markdown("### No Pic")

with col2:

    units = product_df["Quantity_Sold"].sum()
    revenue = product_df["Total_Sales_Baht"].sum()
    fabric = product_df["Fabric"].iloc[0]

    st.metric("Units Sold", f"{units:,}")
    st.metric("Revenue", f"{revenue:,.0f} ฿")
    st.metric("Fabric", fabric)

channel_df = (
    product_df.groupby("sales_Channel")["Quantity_Sold"]
    .sum()
    .reset_index()
)

fig = px.bar(
    channel_df,
    x="sales_Channel",
    y="Quantity_Sold",
    color="sales_Channel",
    title=f"Channel Distribution - {selected_product}"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# CHANNEL PERFORMANCE
# -------------------------

st.subheader("Channel Performance")

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
    title=f"{label} by Channel"
)

st.plotly_chart(fig_channel, use_container_width=True)

# -------------------------
# CHANNEL SHARE
# -------------------------

fig_share = px.pie(
    channel_sales,
    names="sales_Channel",
    values=value_col,
    title="Channel Share"
)

st.plotly_chart(fig_share, use_container_width=True)

# -------------------------
# HEATMAP
# -------------------------

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
    labels={"color": label},
    title="SKU vs Channel Heatmap"
)

st.plotly_chart(fig_heat, use_container_width=True)

# -------------------------
# SKU DEPENDENCY
# -------------------------

dep = (
    df.groupby(["Product_Code", "sales_Channel"])["Quantity_Sold"]
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

st.plotly_chart(fig_dep, use_container_width=True)

# -------------------------
# PARETO
# -------------------------

pareto = (
    df.groupby("Product_Code")[value_col]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

pareto["cum"] = pareto[value_col].cumsum()
pareto["pct"] = pareto["cum"] / pareto[value_col].sum()

fig_pareto = px.line(
    pareto,
    x="Product_Code",
    y="pct",
    markers=True,
    title="SKU Concentration (Pareto)"
)

st.plotly_chart(fig_pareto, use_container_width=True)

# -------------------------
# REPRINT CANDIDATES
# -------------------------

st.subheader("Reprint Candidates")

reprint = (
    df.groupby(["Product_Code", "product_image_url"])["Quantity_Sold"]
    .sum()
    .reset_index()
    .sort_values("Quantity_Sold", ascending=False)
    .head(10)
)

# rename columns for cleaner UI
reprint = reprint.rename(columns={
    "Product_Code": "SKU",
    "product_image_url": "Image",
    "Quantity_Sold": "Units Sold"
})

# add recommendation column
reprint["Priority"] = "High"

st.dataframe(
    reprint,
    column_config={
        "Image": st.column_config.ImageColumn(
            "Product Image"
        ),
        "Units Sold": st.column_config.NumberColumn(
            "Units Sold",
            format="%d"
        )
    },
    hide_index=True,
    use_container_width=True
)

# download button
st.download_button(
    "Download Reprint List",
    reprint.to_csv(index=False),
    file_name="reprint_candidates.csv"
)

# -------------------------
# SLOW MOVERS
# -------------------------

st.subheader("Slow Moving SKU")

slow = (
    df.groupby("Product_Code")["Quantity_Sold"]
    .sum()
    .reset_index()
    .sort_values("Quantity_Sold")
    .head(10)
)

st.dataframe(slow, hide_index=True)