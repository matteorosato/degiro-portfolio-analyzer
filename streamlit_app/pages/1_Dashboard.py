from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from config import FrontendConfig, APIEndpoints, ColumnMappings
from src.api.client import (
    is_backend_alive,
    portfolio_data_exists,
    fetch_portfolio_daily,
    trigger_portfolio_calculation,
    upload_transactions_file
)
from src.components.dashboard_ui import (
    render_header,
    render_product_selector,
    render_metric_selector,
    render_performance_chart,
    render_portfolio_summary,
    render_portfolio_composition
)
from src.data.transformers import prepare_portfolio_dataframe
from src.utils.date_helpers import get_date_range
from src.utils.error_handler import handle_api_error
from src.utils.session_state import initialize_session_state

# Config
st.set_page_config(page_title="Portfolio Dashboard", page_icon=":bar_chart:", layout="centered")

############ APP ############

# Check if backend is alive
if not is_backend_alive():
    st.error("Backend API is not reachable. Please ensure the backend is running.")
    st.stop()

render_header()

# Check if portfolio data exists
if not portfolio_data_exists():
    st.warning("No Degiro transaction data found. Please upload a CSV file to proceed."
               " Check GitHub project documentation for instructions.")
    st.markdown(
        "📖 [Check the GitHub project documentation for instructions](https://github.com/matteorosato/degiro-portfolio-analyzer)"
    )

    uploaded_file = st.file_uploader("Upload your DeGiro transactions CSV file", type=["csv"])

    if uploaded_file:
        with st.spinner("Uploading and processing file..."):
            result = upload_transactions_file(uploaded_file)

        if result and result.get("status") == "success":
            st.success(f"✅ {result['message']}")
            st.info(
                f"Processed {result.get('processed_transactions', 0)} transactions, found {result.get('new_isins', 0)} new ISINs")
            st.rerun()
        else:
            st.error("Failed to upload file. Please try again.")

    st.stop()

# Placeholder for the loading spinner while refreshing data on startup
loading_placeholder = st.empty()

# Initialize session state
initialize_session_state({
    "startup_refresh": False,
    "pending_file_upload": None,
    "show_upload_confirmation": False,
    "upload_count": 0,
    "processing": False,
    "reset_processing": False
})


@st.dialog("Confirm Upload")
def confirm_upload_dialog():
    st.warning("Replace Transactions File?")
    st.markdown(
        "Uploading a new transactions file will replace the existing one and recalculate your entire portfolio. This action cannot be undone.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("OK", use_container_width=True, type="primary"):
            st.session_state.processing = True
            st.rerun()

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.pending_file_upload = None
            st.session_state.upload_count += 1
            st.rerun()

    if st.session_state.get("processing"):
        with st.spinner("Processing and recalculating portfolio..."):
            result = upload_transactions_file(st.session_state.pending_file_upload)

        if result and result.get("status") == "success":
            st.success(f"✅ {result['message']}")
            st.session_state.processing = False
            st.session_state.pending_file_upload = None
            st.session_state.startup_refresh = False
            st.session_state.upload_count += 1
            st.rerun()
        else:
            st.error("Failed to upload file")
            st.session_state.processing = False


@st.dialog("Reset Everything")
def reset_confirm_dialog():
    st.warning("**WARNING: This will delete all portfolio data!**")
    st.markdown("This action **cannot be undone**. Cached calculations will be removed.")

    if st.button("Yes, Reset All", use_container_width=True, type="primary"):
        with st.spinner("Resetting..."):
            try:
                # Call backend to delete all data
                response = requests.delete(
                    FrontendConfig.get_api_url("/debug/delete-all"),
                    timeout=FrontendConfig.API_TIMEOUT
                )
                response.raise_for_status()
                st.success("Reset complete!")
            except Exception as e:
                st.error(f"Reset failed: {e}")

        st.session_state.startup_refresh = False
        st.rerun()

    if st.button("Cancel", use_container_width=True):
        st.rerun()


def refresh_data():
    """Trigger portfolio calculation via API."""
    try:
        trigger_portfolio_calculation()
    except Exception as e:
        st.error(f"Error occurred while refreshing data: {e}")


# Startup refresh logic - Only run initial calculation if no data exists
if not st.session_state.startup_refresh:
    if not portfolio_data_exists():
        # No portfolio data -> Run blocking calculation synchronously
        with st.spinner("Running initial portfolio calculation (this may take some time)..."):
            try:
                trigger_portfolio_calculation()
                st.toast("Initial portfolio calculation completed successfully.")
            except Exception as e:
                st.error(f"Error during portfolio calculation: {e}")

    st.session_state.startup_refresh = True

# Clear the placeholder once the data is ready
loading_placeholder.empty()

# Fetch portfolio data from API
try:
    df = fetch_portfolio_daily()
    df = prepare_portfolio_dataframe(df)
except Exception as e:
    handle_api_error(e, "Failed to fetch portfolio data")

if df.empty:
    st.warning("No portfolio data available.")
    if st.button('Force refresh', type="primary"):
        trigger_portfolio_calculation()
        st.session_state.startup_refresh = False
        st.rerun()
    st.stop()

# Move the file uploader and refresh button to the sidebar
with st.sidebar:
    selected_product, selected_compare_product = render_product_selector(df)
    selected_metric = render_metric_selector(df)

# Filter on product
product_df = df[df['Product'] == selected_product]
compare_product_df = df[
    df['Product'] == selected_compare_product] if selected_compare_product != "None" else pd.DataFrame()

# DATE FILTER    
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

# Use date helpers for date range calculation
selected_start_date, selected_end_date = get_date_range(date_selection, max_date, min_date)

# Filter data by date range
filtered_df = product_df[
    (product_df['End Date'] >= selected_start_date) & (product_df['End Date'] <= selected_end_date)].sort_values(
    by='End Date')

# st.subheader(f"{selected_product}")

# ---- Chart Section ----
render_performance_chart(
    filtered_df,
    selected_metric,
    selected_product,
    compare_product_df,
    selected_compare_product,
    selected_start_date,
    selected_end_date
)

# ---- Portfolio Summary Section ----
if not filtered_df.empty:
    render_portfolio_summary(filtered_df, selected_start_date, selected_end_date)
    st.divider()

    # ---- Portfolio Composition Section ----
    render_portfolio_composition(df, filtered_df)
    st.divider()
else:
    st.write("No data available for the selected product and date range.")

# ---- Additional Metrics Section ----
# st.subheader("Additional Portfolio Metrics")
#
# with st.expander("Data", expanded=False):
#     st.write(filtered_df.drop(columns=['Start Date']))

# File upload in sidebar
with st.sidebar:
    uploaded_file = st.file_uploader("Upload New Transactions CSV", type=["csv"],
                                     key=f"uploader_{st.session_state.upload_count}")

    if uploaded_file is not None:
        st.session_state.pending_file_upload = uploaded_file
        confirm_upload_dialog()

    st.divider()

    if st.button('🔄 Refresh Portfolio Calculation', use_container_width=True,
                 help="Recalculates your portfolio with current data"):
        st.session_state.startup_refresh = False
        with st.spinner("Refreshing data..."):
            refresh_data(None)
        st.success(f"Data updated successfully! (Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        st.session_state.startup_refresh = True
        st.rerun()

    st.divider()

    with st.expander("🔧 Troubleshooting", expanded=False):
        if st.button('⚠️ Reset Everything', use_container_width=True, type="secondary",
                     help="Deletes all cached files AND your transaction data. Restarts the app from scratch."):
            reset_confirm_dialog()
