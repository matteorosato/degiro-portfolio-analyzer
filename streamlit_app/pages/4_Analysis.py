from datetime import timedelta

import pandas as pd
import streamlit as st

from src.api.client import fetch_portfolio_daily
from src.data.transformers import prepare_portfolio_dataframe
from src.utils.error_handler import handle_api_error

# Set the page title
st.set_page_config(page_title="Portfolio Analysis", page_icon="📊", layout="wide")

st.title("Portfolio Analysis")

# Load portfolio data via API
try:
    df = fetch_portfolio_daily()
    df = prepare_portfolio_dataframe(df)
except Exception as e:
    handle_api_error(e, "Failed to load portfolio data")

    df['End Date'] = pd.to_datetime(df['End Date'])
    df = df.sort_values(by='End Date', ascending=True)

    # Remove 'Full Portfolio' entry
    df = df[df["Product"] != "Full portfolio"]

    # Set the default date to most recent end date
    default_selected_date = df['End Date'].max()

    # Date selection
    selected_date = st.date_input("Select End Date", default_selected_date, min_value=df["End Date"].min(),
                                  max_value=df["End Date"].max(), width=250)
    selected_date = pd.to_datetime(selected_date)

    holdings_option = st.segmented_control(
        "Holdings to include",
        options=["Current Holdings", "All Holdings"],
        default="Current Holdings",
        selection_mode="single",
        help="Current Holdings only include products with a non-zero current value"
    )

    filtered_df = df[df['End Date'] <= selected_date]
    if filtered_df.empty:
        st.error("No data found for the selected date. Please select a different date.")
        st.stop()

    # Get the last date and the previous date for daily change calculation
    all_dates = sorted(df['End Date'].unique())
    selected_date_ts = pd.Timestamp(selected_date)

    # Find the index of the selected date (or the closest date before it)
    valid_dates = [d for d in all_dates if d <= selected_date_ts]
    if not valid_dates:
        # If no date before selected_date, use the first date
        date_1 = all_dates[0]
        date_0 = all_dates[0]
    else:
        date_1 = valid_dates[-1]  # Most recent valid date
        date_1_idx = all_dates.index(date_1)
        date_0 = all_dates[date_1_idx - 1] if date_1_idx > 0 else date_1  # Previous date

    # Daily change in current value (1 day: yesterday vs today)
    daily_current_value_start = df[df['End Date'] == date_0]['Current Value (€)'].sum()
    daily_current_value_end = df[df['End Date'] == date_1]['Current Value (€)'].sum()

    if daily_current_value_start != 0:
        daily_current_value_delta = round((daily_current_value_end - daily_current_value_start), 2)
        daily_current_value_delta_eur = f"+€ {abs(daily_current_value_delta)}" if daily_current_value_delta > 0 else f"-€ {abs(daily_current_value_delta)}"
        daily_current_value_delta_per = round(
            ((daily_current_value_end - daily_current_value_start) / daily_current_value_start) * 100, 2)
    else:
        daily_current_value_delta = 0
        daily_current_value_delta_eur = "€ 0"
        daily_current_value_delta_per = 0

    # Current portfolio value (at selected date)
    current_portfolio_value = df[df['End Date'] == date_1]['Current Value (€)'].sum()

    # Filter the DataFrame for the selected date
    selected_day_df = df[df['End Date'] == date_1]

    # Filter based on holdings option
    if holdings_option == "Current Holdings":
        selected_day_df = selected_day_df[selected_day_df["Quantity"] != 0]

    # Prepare display df
    display_df = selected_day_df.copy()

    # Only select relevant columns
    display_df = display_df[['Product', 'Quantity', 'Current Value (€)',
                             'Net Return (€)', 'Net Performance (%)', 'Total Cost (€)'
                             ]]

    # Create new column with 30-day Net Performance (%) trend as list
    date_L30 = date_1 - timedelta(days=30)
    display_df["Net Performance (%) - Trend"] = display_df.apply(
        lambda row: df[
            (df["Product"] == row["Product"]) &
            (df["End Date"] >= date_L30) &
            (df["End Date"] <= date_1)
            ]["Net Performance (%)"].tolist(),
        axis=1
    )

    # Allocation
    display_df["Current Allocation %"] = display_df['Current Value (€)'] / display_df['Current Value (€)'].sum() * 100

    # Sort products by allocation and then by total cost
    display_df = display_df.sort_values(
        by=['Current Allocation %', 'Total Cost (€)'],
        ascending=[False, False]
    )

    df_height_px = 50 * len(display_df) + 37


    # Custom styling function
    def color_net_performance(val):
        color = '#09ab3b' if val > 0 else '#ff2b2b' if val < 0 else 'gray'
        return f'color: {color}'


    # Final column order
    display_df = display_df[['Product', 'Current Allocation %', 'Quantity', 'Current Value (€)',
                             'Net Return (€)', 'Net Performance (%)', 'Net Performance (%) - Trend', 'Total Cost (€)'
                             ]]


    def remove_flat_line(arr):
        if len(arr) == 0:
            return None
        if min(arr) == max(arr):
            return None
        return arr


    display_df["Net Performance (%) - Trend"] = display_df["Net Performance (%) - Trend"].apply(remove_flat_line)

    # Apply Styler to the "Net Performance" columns
    display_df_styled = display_df.style.map(color_net_performance, subset=["Net Performance (%)", "Net Return (€)"])

    # Top badges
    badge_value_color = 'green' if daily_current_value_delta > 0 else 'red' if daily_current_value_delta < 0 else 'gray'
    badge_value_icon = ':material/arrow_upward:' if daily_current_value_delta > 0 else ':material/arrow_downward:' if daily_current_value_delta < 0 else ':material/info:'
    badge_value_text = f"Portfolio Value: € {abs(current_portfolio_value):,.2f} (∆ +{daily_current_value_delta_per}% | {daily_current_value_delta_eur}) " if daily_current_value_delta > 0 \
        else f"Portfolio Value: € {abs(current_portfolio_value):,.2f} (∆ {daily_current_value_delta_per}% | {daily_current_value_delta_eur}) " if daily_current_value_delta < 0 \
        else f"Portfolio Value: € {abs(current_portfolio_value):,.2f}"

    st.markdown(
        f":{badge_value_color}-badge[{badge_value_icon} {badge_value_text}]",
        help="""
**Portfolio Value:** Shows the current portfolio value with the daily change (previous day vs selected date) in euros and percentage.
        """
    )

    # Show dataframe
    st.dataframe(
        display_df_styled,
        height=df_height_px,
        hide_index=True,
        row_height=50,
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

else:
    st.error("Portfolio data not found. Please refresh the dashboard to update the data.")
