import plotly.express as px
import streamlit as st

from src.api.client import fetch_portfolio_daily, fetch_isin_mapping
from src.data.transformers import prepare_portfolio_dataframe, prepare_mapping_dataframe
from src.utils.date_helpers import get_date_range
from src.utils.error_handler import handle_api_error

# Set the page title
st.set_page_config(page_title="Portfolio Analysis - Split", page_icon="📊", layout="centered")

st.title("Portfolio Analysis - Split")

# Load portfolio data via API
try:
    df = fetch_portfolio_daily()
    df = prepare_portfolio_dataframe(df)
except Exception as e:
    handle_api_error(e, "Failed to load portfolio data")

# Load ISIN mapping via API
try:
    mapping = fetch_isin_mapping()
    mapping_df = prepare_mapping_dataframe(mapping)
except Exception as e:
    handle_api_error(e, "Failed to load ISIN mapping")

if not df.empty and not mapping_df.empty:
    df = df.sort_values(by='End Date', ascending=True)

    # Remove 'Full Portfolio' entry
    df = df[df["Product"] != "Full portfolio"]

    # Join product type from mapping_df to df
    merged_df = df.merge(mapping_df[['Ticker', 'Product Type']], left_on='Ticker', right_on='Ticker', how='left')

    # DATE  FILTER    
    # Set the full date range as min and max values for the slider
    max_date = df['End Date'].max().to_pydatetime()
    min_date = df['End Date'].min().to_pydatetime()

    # Date selection
    date_selection = st.segmented_control(
        "Date Range",
        options=["1Y", "3M", "1M", "1W", "YTD", "Last year", "Last month", "All time"],
        default="1Y",
        selection_mode="single",
    )

    # Use date helpers for date range calculation
    selected_start_date, selected_end_date = get_date_range(date_selection, max_date, min_date)

    # Filter data by date range
    filtered_df = merged_df[
        (merged_df['End Date'] >= selected_start_date) & (merged_df['End Date'] <= selected_end_date)].sort_values(
        by='End Date')

    # METRIC FILTER
    # Performance metrics
    performance_metrics = ["Net Performance (%)", "Net Return (€)", "Total Cost (€)", "Current Value (€)"]
    default_index_per = performance_metrics.index("Current Value (€)")
    selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per,
                                   key="metric_select", width=250)

    # Group by Product Type and aggregate Net Return (€) and Total Cost (€)
    split_df = (
        filtered_df.groupby(["End Date", "Product Type"])[["Net Return (€)", "Total Cost (€)", "Current Value (€)"]]
        .sum()
        .reset_index()
        .sort_values(by=["End Date", "Product Type"], ascending=False)
    )

    # Add metrics after grouping
    split_df["Net Performance (%)"] = (split_df["Net Return (€)"] / split_df["Total Cost (€)"]) * 100 if split_df[
        "Total Cost (€)"].any() else 0

    # Round all columns to 2 decimal places
    split_df = split_df.round({
        "Net Return (€)": 2,
        "Total Cost (€)": 2,
        "Current Value (€)": 2,
        "Net Performance (%)": 2
    })

    # Color mapping plots
    product_type_colors = {
        "ETF": "#1f77b4",
        "Stock": "orange",
        "Other": "purple"
    }

    st.subheader(f"{selected_metric} Over Time by Product Type")

    # Plot
    fig = px.line()  # Empty figure

    # Loop over each product type and add a line
    for product_type in split_df["Product Type"].unique():
        product_data = split_df[split_df["Product Type"] == product_type]

        fig.add_scatter(
            x=product_data["End Date"],
            y=product_data[selected_metric],
            mode="lines",
            name=product_type,
            line=dict(shape='spline', smoothing=0.7,
                      color=product_type_colors.get(product_type, "#888"))
        )

    # Add dashed line at y=0
    if (split_df[selected_metric] < 0).any():
        fig.add_shape(
            type="line",
            x0=split_df["End Date"].min(),
            x1=split_df["End Date"].max(),
            y0=0,
            y1=0,
            line=dict(
                color="black",
                width=1,
                dash="dash"
            ),
            xref="x",
            yref="y"
        )

    # Layout adjustments
    fig.update_layout(
        width=1200,
        height=400,
        margin=dict(l=0, r=0, t=50, b=50),
        showlegend=True,
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", yanchor="bottom")
    )

    st.plotly_chart(fig, use_container_width=False)

    st.divider()

    st.subheader(f"{selected_metric} Split by Product Type")

    # Filter the latest day only
    latest_day_df = split_df[split_df["End Date"] == selected_end_date]

    # Check for negative values in the selected metric
    if (latest_day_df[selected_metric] < 0).any():
        # Use bar chart if any value is negative
        bar_fig = px.bar(
            latest_day_df,
            x="Product Type",
            y=selected_metric,
            color="Product Type",
            color_discrete_map=product_type_colors,
            text=selected_metric
        )
        bar_fig.update_layout(showlegend=False)
        bar_fig.update_layout(bargap=0.4, height=350, margin=dict(l=0, r=0, t=25, b=0))
        st.plotly_chart(bar_fig, use_container_width=True)

    else:
        # Use pie chart if all values are positive
        pie_fig = px.pie(
            latest_day_df,
            names="Product Type",
            values=selected_metric,
            hole=0.5,
            color="Product Type",
            color_discrete_map=product_type_colors
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        pie_fig.update_layout(showlegend=False)
        pie_fig.update_layout(height=350, margin=dict(l=0, r=0, t=25, b=0))
        st.plotly_chart(pie_fig, use_container_width=True)


else:
    st.error(
        "Portfolio data not found. Please run the 'dashboard' page first to generate the portfolio performance data.")
    st.stop()
