from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from config import FrontendConfig, APIEndpoints, ColumnMappings

# Config
st.set_page_config(page_title="Portfolio Dashboard", page_icon=":bar_chart:", layout="centered")


def is_backend_alive():
    try:
        response = requests.get(FrontendConfig.API_BASE_URL, timeout=2)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def portfolio_data_exists():
    """Check if portfolio data is available via API."""
    try:
        response = requests.get(
            FrontendConfig.get_api_url(APIEndpoints.PORTFOLIO_DAILY),
            timeout=5
        )
        return response.status_code == 200
    except:
        return False


# Backend triggers
def trigger_portfolio_calculation():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    response = requests.post(
        FrontendConfig.get_api_url(APIEndpoints.PORTFOLIO_CALCULATE),
        timeout=FrontendConfig.API_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def upload_csv_file(uploaded_file):
    """Upload CSV file to backend via API."""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
        response = requests.post(
            FrontendConfig.get_api_url(APIEndpoints.TRANSACTIONS_UPLOAD),
            files=files,
            timeout=FrontendConfig.API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to upload file: {e}")
        return None


def get_portfolio_daily():
    """Fetch daily portfolio data from API."""
    try:
        response = requests.get(
            FrontendConfig.get_api_url(APIEndpoints.PORTFOLIO_DAILY),
            timeout=FrontendConfig.API_TIMEOUT
        )
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except requests.RequestException as e:
        st.error(f"Failed to fetch portfolio data: {e}")
        return pd.DataFrame()


def get_isin_mapping():
    """Fetch ISIN mapping from API."""
    try:
        response = requests.get(
            FrontendConfig.get_api_url(APIEndpoints.PORTFOLIO_ISIN_MAPPING),
            timeout=FrontendConfig.API_TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to fetch ISIN mapping: {e}")
        return {}


############ APP ############

# Check if backend is alive
if not is_backend_alive():
    st.error("Backend API is not reachable. Please ensure the backend is running.")
    st.stop()

st.title("Portfolio Dashboard")

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
            result = upload_csv_file(uploaded_file)

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

# Define startup refresh state variable
if st.session_state.get("startup_refresh") is None:
    st.session_state.startup_refresh = False
if st.session_state.get("pending_file_upload") is None:
    st.session_state.pending_file_upload = None
if st.session_state.get("show_upload_confirmation") is None:
    st.session_state.show_upload_confirmation = False
if st.session_state.get("upload_count") is None:
    st.session_state.upload_count = 0
if st.session_state.get("processing") is None:
    st.session_state.processing = False
if st.session_state.get("reset_processing") is None:
    st.session_state.reset_processing = False


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
            result = upload_csv_file(st.session_state.pending_file_upload)

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


# Startup refresh logic
if not st.session_state.startup_refresh:
    if portfolio_data_exists():
        # Portfolio exists -> trigger background refresh
        try:
            response = requests.post(
                FrontendConfig.get_api_url(APIEndpoints.PORTFOLIO_REFRESH),
                timeout=FrontendConfig.API_TIMEOUT
            )
            response.raise_for_status()
            st.toast("Data refreshed successfully.")
        except requests.exceptions.RequestException as e:
            st.error(f"Error during data refreshing process: {e}")
    else:
        # No portfolio data -> Run blocking calculation synchronously
        with st.spinner("Running initial portfolio calculation (this may take some time)..."):
            try:
                refresh_data()
                st.toast("Initial portfolio calculation completed successfully.")
            except Exception as e:
                st.error(f"Error during portfolio calculation: {e}")

    st.session_state.startup_refresh = True

# Clear the placeholder once the data is ready
loading_placeholder.empty()

# Dictionary to rename the performance metrics columns for display purposes
rename_dict = ColumnMappings.PORTFOLIO_RENAME

# Fetch portfolio data from API
df = get_portfolio_daily()

if df.empty:
    st.warning("No portfolio data available.")
    if st.button('Force refresh', type="primary"):
        trigger_portfolio_calculation()
        st.session_state.startup_refresh = False
        st.rerun()
    st.stop()

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

# Get min_date from the FIRST TRANSACTION via API
try:
    response = requests.get(
        FrontendConfig.get_api_url(APIEndpoints.TRANSACTIONS_ALL),
        timeout=FrontendConfig.API_TIMEOUT
    )
    response.raise_for_status()
    transactions_data = response.json()

    if transactions_data:
        transactions_df = pd.DataFrame(transactions_data)
        transactions_df['Date'] = pd.to_datetime(transactions_df['Date'])
        first_transaction_date = transactions_df['Date'].min().to_pydatetime()
        min_date = first_transaction_date
    else:
        min_date = df['End Date'].min().to_pydatetime()
except Exception as e:
    st.warning(f"Could not load first transaction date: {e}. Using portfolio min date.")
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

    # Calculate net cash flows during the period (cost invested in the period)
    # Total Cost is cumulative, so the difference tells us how much was invested/withdrawn
    net_cash_flows_period = period_end_cost - period_start_cost

    # Calculate Period Return in € considering cash flows
    # Period Return = (End Value - Start Value) - Net Cash Invested
    # This shows the actual gain/loss excluding the effect of new money added
    period_return_euro = period_end_value - period_start_value - net_cash_flows_period

    # Calculate Period Performance %
    # Performance % = Period Return / (Start Value + Net Cash Invested) * 100
    # We use the average capital employed during the period
    if period_start_value + net_cash_flows_period != 0:
        period_performance_pct = (period_return_euro / (period_start_value + net_cash_flows_period)) * 100
    else:
        period_performance_pct = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        # Portfolio Value: current value at end of period
        st.metric(
            label="Portfolio Value",
            value=f"€ {period_end_value:,.2f}",
        )
    with col2:
        # Period Return: gain/loss in € after accounting for cash flows
        # Formula: (End Value - Start Value) - Net Cash Invested
        # Shows the actual profit/loss excluding the effect of new money added
        st.metric(
            label="Period Return",
            value=f"€ {period_return_euro:,.2f}"
        )
    with col3:
        # Period Performance: return as percentage with +/- sign
        performance_sign = "+" if period_performance_pct >= 0 else ""
        st.metric(
            label="Period Performance",
            value=f"{performance_sign}{period_performance_pct:.2f}%"
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
