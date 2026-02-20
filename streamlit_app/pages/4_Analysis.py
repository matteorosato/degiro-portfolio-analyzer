import pandas as pd
import streamlit as st

from src.api.client import fetch_portfolio_daily
from src.data.transformers import prepare_portfolio_dataframe
from src.utils.error_handler import handle_api_error
from src.utils.styling import color_net_performance
from src.utils.data_helpers import remove_flat_line, filter_full_portfolio
from src.utils.formatting import format_portfolio_badge
from src.services.analysis_service import (
    find_valid_dates,
    calculate_daily_change,
    prepare_display_dataframe,
)
from config import UIConstants

# Set the page title
st.set_page_config(page_title="Portfolio Analysis", page_icon="📊", layout="wide")

st.title("Portfolio Analysis")

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

df['End Date'] = pd.to_datetime(df['End Date'])
df = df.sort_values(by='End Date', ascending=True)

# Remove 'Full Portfolio' entry
df = filter_full_portfolio(df)

# ============================================================================
# USER INPUT
# ============================================================================

# Set the default date to most recent end date
default_selected_date = df['End Date'].max()

# Date selection
selected_date = st.date_input(
    "Select End Date",
    default_selected_date,
    min_value=df["End Date"].min(),
    max_value=df["End Date"].max()
)
selected_date = pd.to_datetime(selected_date)

# Holdings filter
holdings_option = st.segmented_control(
    "Holdings to include",
    options=UIConstants.HOLDINGS_OPTIONS,
    default="Current Holdings",
    selection_mode="single",
    help="All Holdings also include products that are no longer held in the portfolio"
)

# ============================================================================
# DATA PROCESSING
# ============================================================================

# Verify data availability
filtered_df = df[df['End Date'] <= selected_date]
if filtered_df.empty:
    st.error("No data found for the selected date. Please select a different date.")
    st.stop()

# Find valid dates for daily change calculation
all_dates = sorted(df['End Date'].unique())
date_1, date_0 = find_valid_dates(all_dates, pd.Timestamp(selected_date))

# Calculate daily change metrics
daily_metrics = calculate_daily_change(df, date_1, date_0)

# Prepare display DataFrame
display_df = prepare_display_dataframe(df, date_1, holdings_option)

# Remove flat trends
display_df["Net Performance (%) - Trend"] = display_df["Net Performance (%) - Trend"].apply(remove_flat_line)

# Apply styling
display_df_styled = display_df.style.map(
    color_net_performance,
    subset=["Net Performance (%)", "Net Return (€)"]
)

# ============================================================================
# UI DISPLAY
# ============================================================================

# Portfolio value badge
badge_color, badge_icon, badge_text = format_portfolio_badge(
    daily_metrics["current_value"],
    daily_metrics["daily_delta"],
    daily_metrics["daily_delta_per"]
)

st.markdown(
    f":{badge_color}-badge[{badge_icon} {badge_text}]",
    help="**Portfolio Value:** Shows the current portfolio value and the last daily change"
)

# Calculate table height
df_height_px = UIConstants.calculate_table_height(len(display_df))

# Show dataframe
st.dataframe(
    display_df_styled,
    height=df_height_px,
    hide_index=True,
    column_config={
        "Product": st.column_config.TextColumn(
            "Product",
            width="medium",
            pinned=True,
        ),
        "Current Allocation %": st.column_config.ProgressColumn(
            "Allocation (%)",
            format="%.1f%%",
            min_value=0,
            max_value=100,
            width="small",
            help="Current allocation percentage of the product in the portfolio (product current value / total current value)."
        ),
        "Current Value (€)": st.column_config.NumberColumn(
            "Current Value (€)",
            format="€ %.2f",
            width="small",
        ),
        "Net Return (€)": st.column_config.NumberColumn(
            "Profit/Loss (€)",
            format="€ %.2f",
            width="small",
        ),
        "Total Cost (€)": st.column_config.NumberColumn(
            "Total Cost (€)",
            format="€ %.2f",
            width="small"
        ),
        "Quantity": st.column_config.NumberColumn(
            "Quantity",
            format="%d",
            width="small"
        ),
        "Net Performance (%)": st.column_config.NumberColumn(
            "Profit/Loss (%)",
            format="%.2f%%",
            width="small"
        ),
        "Net Performance (%) - Trend": st.column_config.AreaChartColumn(
            "30-day P/L (%)",
            width="small"
        )
    }
)