import streamlit as st

from src.api.client import fetch_portfolio_daily, fetch_isin_mapping
from src.data.transformers import prepare_portfolio_dataframe, prepare_mapping_dataframe
from src.utils.date_helpers import get_date_range
from src.utils.error_handler import handle_api_error
from src.utils.data_helpers import (
    filter_full_portfolio,
    enrich_with_product_type,
    aggregate_by_product_type,
    calculate_net_performance,
    round_financial_columns,
)
from src.utils.chart_helpers import create_line_chart_by_type, create_split_chart
from config import UIConstants

# Set the page title
st.set_page_config(page_title="Portfolio Analysis - Split", page_icon="📊", layout="centered")

st.title("Portfolio Analysis - Split")

# ============================================================================
# DATA LOADING
# ============================================================================

# Load portfolio data via API
try:
    df = fetch_portfolio_daily()
    df = prepare_portfolio_dataframe(df)
except Exception as e:
    handle_api_error(e, "Failed to load portfolio data")
    st.stop()

# Load ISIN mapping via API
try:
    mapping = fetch_isin_mapping()
    mapping_df = prepare_mapping_dataframe(mapping)
except Exception as e:
    handle_api_error(e, "Failed to load ISIN mapping")
    st.stop()

# ============================================================================
# DATA PROCESSING
# ============================================================================

if df.empty or mapping_df.empty:
    st.error(
        "Portfolio data not found. Please run the 'dashboard' page first to generate the portfolio performance data."
    )
    st.stop()

# Sort and filter
df = df.sort_values(by='End Date', ascending=True)
df = filter_full_portfolio(df)

# Enrich with product type
df = enrich_with_product_type(df, mapping_df)

# Get date range
max_date = df['End Date'].max().to_pydatetime()
min_date = df['End Date'].min().to_pydatetime()

# ============================================================================
# USER INPUT
# ============================================================================

# Date range selection
date_selection = st.segmented_control(
    "Date Range",
    options=UIConstants.DATE_RANGE_OPTIONS,
    default="1Y",
    selection_mode="single",
)

# Performance metric selection
performance_metrics = ["Net Performance (%)", "Net Return (€)", "Total Cost (€)", "Current Value (€)"]
default_index_per = performance_metrics.index("Current Value (€)")
selected_metric = st.selectbox(
    "Select a Performance Metric",
    options=performance_metrics,
    index=default_index_per,
    key="metric_select"
)

# ============================================================================
# DATA PREPARATION
# ============================================================================

# Get date range based on selection
selected_start_date, selected_end_date = get_date_range(date_selection, max_date, min_date)

# Filter by date range
filtered_df = df[
    (df['End Date'] >= selected_start_date) & (df['End Date'] <= selected_end_date)
].sort_values(by='End Date')

# Aggregate by product type
split_df = aggregate_by_product_type(filtered_df)

# Calculate net performance
split_df = calculate_net_performance(split_df)

# Round financial columns
split_df = round_financial_columns(split_df)

# ============================================================================
# CHARTS
# ============================================================================

st.subheader(f"{selected_metric} Over Time by Product Type")

# Line chart
line_fig = create_line_chart_by_type(split_df, selected_metric)
st.plotly_chart(line_fig, use_container_width=False)

st.divider()

st.subheader(f"{selected_metric} Split by Product Type")

# Get latest day data
latest_day_df = split_df[split_df["End Date"] == selected_end_date]

# Split chart (pie or bar)
split_fig = create_split_chart(latest_day_df, selected_metric)
st.plotly_chart(split_fig, use_container_width=True)
