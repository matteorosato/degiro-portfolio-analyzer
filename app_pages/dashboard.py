import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from backend.utils.api import post_api_request

OUTPUT_DIR = "output"
LOG_DIR = "logs"
UPLOADS_DIR = "uploads"

# Config
st.set_page_config(page_title="Degiro Portfolio Analyzer", page_icon=":bar_chart:", layout="centered")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")  # Use environment variable for API URL


def is_backend_alive():
    try:
        response = requests.get(API_BASE_URL, timeout=2)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def cached_files_exist():
    cached_files = [
        os.path.join(OUTPUT_DIR, 'portfolio_performance_daily.parquet'),
        os.path.join(OUTPUT_DIR, 'stock_prices.parquet')
    ]
    return all(os.path.exists(f) for f in cached_files)


# Backend triggers
def trigger_portfolio_calculation():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return post_api_request(
        f"{API_BASE_URL}/portfolio/calculate"
    )


def trigger_db_refresh():
    return post_api_request(
        f"{API_BASE_URL}/db/refresh",
        success_message="Database refresh triggered successfully."
    )


def initial_db_load():
    return post_api_request(
        f"{API_BASE_URL}/db/initial-db-load"
    )


############ APP ############


def get_log_files():
    if not os.path.exists(LOG_DIR):
        return []
    return [f for f in os.listdir(LOG_DIR) if os.path.isfile(os.path.join(LOG_DIR, f))]


def read_last_n_lines_reversed(filename, n=100):
    with open(os.path.join(LOG_DIR, filename), 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return "".join(lines[-n:][::-1])


with st.sidebar.expander("View Logs", expanded=False):
    log_files = get_log_files()
    if not log_files:
        st.info("No log files found.")
    else:
        selected_log = st.selectbox("Select log file", options=[""] + log_files,
                                    format_func=lambda x: x or "— Select a file —")
        if selected_log:
            content = read_last_n_lines_reversed(selected_log, 100)
            st.text_area(f"Contents of {selected_log} (most recent first)", content, height=300)

# Check if backend is alive
if not is_backend_alive():
    st.error("Backend API is not reachable. Please ensure the backend is running.")
    st.stop()  # Stop execution if backend is not reachable

st.title("Degiro Portfolio Analyzer")

# Ensure the uploads directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)

# List CSV files in the uploads directory
csv_files = [f for f in os.listdir(UPLOADS_DIR) if f.lower().endswith(".csv")]

# Check if any transaction CSV files are present
if not csv_files:
    st.warning("No Degiro transaction data found. Please upload a CSV file to proceed."
               " Check GitHub project documentation for instructions.")
    st.markdown(
        "📖 [Check the GitHub project documentation for instructions](https://github.com/matteorosato/degiro-portfolio-analyzer)"
    )

    uploaded_file = st.file_uploader("Upload your DeGiro transactions CSV file", type=["csv"])

    if uploaded_file:
        # Save the uploaded file to the desired location
        file_path = os.path.join(UPLOADS_DIR, 'Transactions.csv')
        df = pd.read_csv(uploaded_file)
        df.to_csv(file_path, index=False)

        # Inform the user that the page will be reloaded
        st.success("File uploaded successfully! The page will reload to apply the changes.")

        # Trigger the page reload (rerun the app)
        st.rerun()

    st.stop()  # Stop execution if no data is available

# Placeholder for the loading spinner while refreshing data on startup
loading_placeholder = st.empty()

# Define startup refresh state variable
if st.session_state.get("startup_refresh") is None:
    st.session_state.startup_refresh = False  # Indicates refresh hasn't been run yet


def refresh_data(uploaded_file=None):
    # Check for new transactions file
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if df.empty:
            st.error("The uploaded file is empty after reading.")
            return
        transaction_file = os.path.join(UPLOADS_DIR, 'Transactions.csv')
        df.to_csv(transaction_file, index=False)
        st.success(f"Data saved to {transaction_file}")

    # Trigger the backend API to refresh data
    try:
        # Check if initial db load is needed
        initial_db_load()
        trigger_portfolio_calculation()
        if st.session_state.startup_refresh:
            st.success(f"Data updated successfully! (Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

    except Exception as e:
        st.error(f"Error occurred while refreshing data: {e}")


def clear_cache():
    cached_files = [
        os.path.join(OUTPUT_DIR, filename)
        for filename in [
            'portfolio_performance_monthly.parquet',
            'portfolio_performance_daily.parquet',
            'stock_prices.parquet'
        ]
    ]

    if not cached_files:
        st.warning("No cached files found to clear.")
        return

    deleted_files = []
    for file_path in cached_files:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                basename = os.path.basename(file_path)
                deleted_files.append(basename)
                st.info(f"Deleted {basename}")
            else:
                st.warning(f"File not found: {file_path}")
        except Exception as e:
            st.error(f"Error deleting {file_path}: {e}")


# Startup refresh logic
if not st.session_state.startup_refresh:

    if cached_files_exist():
        try:
            response = requests.post(f"{API_BASE_URL}/portfolio/refresh")
            response.raise_for_status()  # Catching eventual errors
            st.toast("Data refreshed successfully.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error during data refreshing process: {e}")
    else:
        # No cached files -> Run blocking calculation synchronously
        with st.spinner("No cached data found. Running initial portfolio calculation..."):
            try:
                refresh_data()
                st.toast("Initial portfolio calculation completed successfully.")
            except Exception as e:
                st.error(f"Error during portfolio calculation: {e}")

    # Ensure startup refresh flag is set to True after either process
    st.session_state.startup_refresh = True

# Clear the placeholder once the data is ready
loading_placeholder.empty()

# Dictionary to rename the performance metrics columns for display purposes
rename_dict = {
    'product': 'Product',
    'ticker': 'Ticker',
    'quantity': 'Quantity',
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'avg_cost': 'Average Cost (€)',
    'total_cost': 'Total Cost (€)',
    'transaction_costs': 'Transaction Costs (€)',
    'current_value': 'Current Value (€)',
    'current_money_weighted_return': 'Current Money Weighted Return (€)',
    'realized_return': 'Realized Return (€)',
    'net_return': 'Net Return (€)',
    'current_performance_percentage': 'Current Performance (%)',
    'net_performance_percentage': 'Net Performance (%)'
}

portfolio_performance_file = os.path.join(OUTPUT_DIR, 'portfolio_performance_daily.parquet')

# Check if the file exists before trying to load it
if os.path.exists(portfolio_performance_file):
    try:
        # Load daily data
        df = pd.read_parquet(portfolio_performance_file)

        # If df is empty
        if df.empty:
            if st.button('Force refresh', type="primary"):
                trigger_portfolio_calculation()
                st.session_state.startup_refresh = False
                st.rerun()

    except Exception as e:
        # General exception handling
        st.warning(f"Failed loading data. Are the stock tickers mapped correctly? Error details: {str(e)}")
        st.page_link("app_pages/ticker_mapping.py", label="Click here to check ticker mapping", icon="ℹ️")
        st.markdown(
            "📖 [Check the GitHub project documentation for instructions](https://github.com/matteorosato/degiro-portfolio-analyzer/blob/main/README.md)"
        )
        if st.button('Clear Cached Data', type="primary"):
            clear_cache()
            st.session_state.startup_refresh = False
            st.rerun()
        st.stop()

else:
    # Handle case where the file doesn't exist
    st.warning("The portfolio data file is missing. Creating it for the first time...")
    trigger_portfolio_calculation()  # This will create the missing file
    # st.session_state.startup_refresh = False
    # st.rerun()  # Reload the page to read the new file

df = pd.read_parquet(portfolio_performance_file)
# Rename columns
df = df.rename(columns=rename_dict)

# Convert dates to datetime format
df['Start Date'] = pd.to_datetime(df['Start Date'])
df['End Date'] = pd.to_datetime(df['End Date'])

# Move the file uploader and refresh button to the sidebar
with st.sidebar:
    # Sort product options
    product_options = sorted(df['Product'].unique().tolist())
    if "Full portfolio" in product_options:
        product_options.remove("Full portfolio")
        product_options.insert(0, "Full portfolio")

    # Set default index for "Full Portfolio"
    default_index = product_options.index("Full portfolio")
    selected_product = st.selectbox("Select a Product", options=product_options, index=default_index,
                                    key="product_select")

    # Dropdown to select another product for comparison
    compare_product_options = ["None"] + product_options
    selected_compare_product = st.selectbox("Compare with another Product", options=compare_product_options, index=0,
                                            key="compare_product_select")

    # Performance metrics
    performance_metrics = [col for col in df.columns if col not in ['Product', 'Ticker', 'Start Date', 'End Date']]
    default_index_per = performance_metrics.index("Current Value (€)")
    selected_metric = st.selectbox("Select a Performance Metric", options=performance_metrics, index=default_index_per,
                                   key="metric_select")

# Filter on product
product_df = df[df['Product'] == selected_product]
compare_product_df = df[
    df['Product'] == selected_compare_product] if selected_compare_product != "None" else pd.DataFrame()

# DATE  FILTER    
# Set the full date range as min and max values for the slider
max_date = df['End Date'].max().to_pydatetime()
min_date = df['End Date'].min().to_pydatetime()

# Date selection
date_selection = st.segmented_control(
    "Date Range",
    options=["1Y", "3M", "1M", "1W", "YTD", "Last year", "Last month", "All time"],
    default="All time",
    selection_mode="single",
)

# Key date anchors
first_day_this_year = max_date.replace(month=1, day=1)
first_day_this_month = max_date.replace(day=1)

# Days since start of this year/month
days_since_year_start = (max_date - first_day_this_year).days
days_since_month_start = (max_date - first_day_this_month).days

# Previous month range
last_day_prev_month = first_day_this_month - timedelta(days=1)
first_day_prev_month = last_day_prev_month.replace(day=1)
days_in_last_month = (last_day_prev_month - first_day_prev_month).days + 1

# Previous year range
first_day_prev_year = first_day_this_year.replace(year=max_date.year - 1)
last_day_prev_year = first_day_prev_year.replace(month=12, day=31)
days_in_last_year = (last_day_prev_year - first_day_prev_year).days + 1

# Final mapping
date_mapping = {
    "1Y": [365, 0],
    "3M": [90, 0],
    "1M": [30, 0],
    "1W": [7, 0],
    "1D": [1, 0],
    "YTD": [days_since_year_start, 0],
    "Last year": [days_in_last_year + days_since_year_start, days_since_year_start + 1],  # +1 to exclude Jan 1
    "Last month": [days_in_last_month + days_since_month_start, days_since_month_start + 1],
    # +1 to exclude 1st of current month
    "All time": [(max_date - min_date).days, 0]
}

selected_start_date = max_date - timedelta(days=date_mapping[date_selection][0])
selected_end_date = max_date - timedelta(days=date_mapping[date_selection][1])

# Filter data by date range
filtered_df = product_df[
    (product_df['End Date'] >= selected_start_date) & (product_df['End Date'] <= selected_end_date)].sort_values(
    by='End Date')

# st.subheader(f"{selected_product}")

# ---- Chart Section ----
if not filtered_df.empty:
    st.subheader(f"{selected_metric} for {selected_product}")

    # Plot
    fig = px.line()

    # Add the first trace (main product)
    fig.add_scatter(
        x=filtered_df['End Date'],
        y=filtered_df[selected_metric],
        mode='lines',
        name=f"{selected_product}",
        line=dict(color="#1f77b4", shape='spline', smoothing=0.7)
    )

    # Add comparison line if another product is selected
    if not compare_product_df.empty:
        compare_filtered_df = compare_product_df[
            (compare_product_df['End Date'] >= selected_start_date) &
            (compare_product_df['End Date'] <= selected_end_date)
            ].sort_values(by='End Date')

        fig.add_scatter(
            x=compare_filtered_df['End Date'],
            y=compare_filtered_df[selected_metric],
            mode='lines',
            name=f"{selected_compare_product}",
            line=dict(color='orange', shape='spline', smoothing=0.7)
        )

        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", yanchor="bottom")
        )

    fig.update_layout(width=1200, height=400, margin=dict(l=0, r=0, t=50, b=50))
    st.plotly_chart(fig, use_container_width=False)

    # ---- Portfolio Summary Section ----
    # Format the date range for the title
    period_start_str = selected_start_date.strftime('%Y-%m-%d')
    period_end_str = selected_end_date.strftime('%Y-%m-%d')
    st.subheader(f"Portfolio Summary")
    st.caption(f"Period: {period_start_str} to {period_end_str} "
               f"({(selected_end_date - selected_start_date).days} days)")

    # Get values at the start and end of the selected period
    period_start_value = filtered_df.iloc[0].get("Current Value (€)", 0) if len(filtered_df) > 0 else 0
    period_start_cost = filtered_df.iloc[0].get("Total Cost (€)", 0) if len(filtered_df) > 0 else 0

    period_end_value = filtered_df.iloc[-1].get("Current Value (€)", 0)
    period_end_cost = filtered_df.iloc[-1].get("Total Cost (€)", 0)

    # Calculate return for the selected period
    # Return = (End Value - Start Value) + (End Cost - Start Cost) since cost changes with transactions
    period_return = (period_end_value - period_start_value) - (period_end_cost - period_start_cost)
    period_return_pct = ((period_end_value / period_end_cost * 100) - 100) if period_end_cost != 0 else 0

    # Total Return display
    total_return_display = f"€ {period_return:,.2f}"

    # Annualized return calculation for the selected period
    start_date = filtered_df['Start Date'].min()
    end_date = filtered_df['End Date'].max()
    days_held = (end_date - start_date).days
    if period_end_cost > 0 and days_held > 0:
        if period_end_value <= 0:
            annualized_return_pct = -100  # default negative percentage
        else:
            annualized_return_pct = (
                    ((period_end_value / period_end_cost) ** (365 / days_held) - 1) * 100
            )
    else:
        annualized_return_pct = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Portfolio Value",
            value=f"€ {period_end_value:,.2f}",
        )
    with col2:
        st.metric(
            label="Period Return",
            value=total_return_display,
            delta=f"{period_return_pct:.2f} %"
        )
    with col3:
        st.metric(
            label="Annualized Return (CAGR)",
            value=f"{annualized_return_pct:.2f} %"
        )

    st.divider()

    # ---- Portfolio Composition Section ----
    st.subheader("Portfolio Composition")

    # Get the latest data for all products in the selected period
    latest_date = filtered_df['End Date'].max()
    composition_df = df[df['End Date'] == latest_date].copy()

    # Filter out "Full portfolio" from the composition
    composition_df = composition_df[composition_df['Product'] != 'Full portfolio']

    if not composition_df.empty and len(composition_df) > 0:
        # Calculate NAV and NAV % for each product
        composition_df['NAV'] = composition_df['Current Value (€)']
        total_nav = composition_df['NAV'].sum()
        composition_df['NAV %'] = (composition_df['NAV'] / total_nav * 100) if total_nav > 0 else 0

        # Prepare data for display
        composition_display = composition_df[['Product', 'NAV', 'NAV %']].copy()
        composition_display = composition_display.sort_values('NAV', ascending=False)

        # Display table first
        st.dataframe(
            composition_display.style.format({
                'NAV': '€ {:,.2f}',
                'NAV %': '{:.2f}%'
            }),
            hide_index=True,
            use_container_width=True
        )

        # Create pie chart (displayed below the table)
        fig_pie = px.pie(
            composition_display,
            values='NAV',
            names='Product'
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No composition data available. Select 'Full portfolio' to see individual holdings.")

    st.divider()
else:
    st.write("No data available for the selected product and date range.")

# ---- Additional Metrics Section ----
# st.subheader("Additional Portfolio Metrics")
#
# with st.expander("Data", expanded=False):
#     st.write(filtered_df.drop(columns=['Start Date']))

# File upload
with st.sidebar:
    # File uploader for the user to upload a new CSV file
    uploaded_file = st.file_uploader("Upload New Transactions CSV", type=["csv"])

    # Refresh Button to update the CSV
    if st.button('Refresh Data'):
        st.session_state.startup_refresh = False
        refresh_data(uploaded_file)
        st.rerun()

    if st.button('Clear Cached Data', type="primary"):
        clear_cache()
        st.session_state.startup_refresh = False
        st.rerun()

    # # Refresh Button to refresh database if env variable is set to true
    # if os.getenv("USE_SUPABASE", "true").lower() == "true":
    #     if st.button('Refresh Database'):
    #         st.info("Upserting cached data to database and refreshing locally cached data. This will take some time.")
    #         # Run db_refresh (API) to update the CSV
    #         try:
    #             trigger_db_refresh()
    #             if st.session_state.startup_refresh:
    #                 st.success(f"Database refreshed successfully! (Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    #         except Exception as e:
    #             st.error(f"Error occurred while refreshing database: {e}")
    #         st.session_state.startup_refresh = False
    #         st.rerun()
