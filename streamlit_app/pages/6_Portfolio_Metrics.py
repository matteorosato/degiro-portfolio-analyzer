"""
Portfolio Metrics Page - Dashboard at a Glance

Modern, visually engaging dashboard with:
- Sticky period selector at top
- 3×3 grid of metric cards
- Holdings & capital flows section
- Responsive design

Default period: All Time
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

import streamlit as st

from streamlit_app.config import FrontendConfig
from streamlit_app.src.api.client import is_backend_alive, portfolio_data_exists
from streamlit_app.src.data.transformers import prepare_portfolio_dataframe
from streamlit_app.src.utils.error_handler import handle_api_error
from streamlit_app.src.utils.formatting import format_currency, format_percentage

# Page configuration
st.set_page_config(
    page_title="Portfolio Metrics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

API_BASE_URL = FrontendConfig.API_BASE_URL
API_V1_PREFIX = FrontendConfig.API_V1_PREFIX

PERIOD_PRESETS = {
    "1Y": (-365, 0),
    "3M": (-90, 0),
    "1M": (-30, 0),
    "YTD": "ytd",
    "Last year": "last_year",
    "Last month": "last_month",
    "All time": "all_time",
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_color_delta(value: float) -> str:
    """Return appropriate color for positive/negative value."""
    if value > 0:
        return "🟢"
    elif value < 0:
        return "🔴"
    else:
        return "⚪"


def get_delta_color_for_value(value: float) -> str:
    """Return 'off' for neutral, 'normal' for color coding."""
    if value == 0:
        return "off"
    return "normal"


def render_metric_card(
        icon: str,
        title: str,
        value: str,
        context: str = "",
        delta: str = "",
        delta_color: bool = False,
        color_value: float = 0
):
    """Render a single metric card with consistent styling."""
    color_class = ""
    if delta and delta_color:
        if "+" in delta or "🟢" in delta:
            color_class = "positive"
        elif "-" in delta or "🔴" in delta:
            color_class = "negative"
    elif color_value != 0:  # Apply color based on value if no delta
        if color_value > 0:
            color_class = "positive"
        elif color_value < 0:
            color_class = "negative"

    html = f"""
    <div class="metric-card {color_class}">
        <div class="metric-header">
            <span class="metric-icon">{icon}</span>
            <span class="metric-title">{title}</span>
        </div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-context">{context}</div>' if context else ''}
        {f'<div class="metric-delta">{delta}</div>' if delta else ''}
    </div>
    """
    return html


@st.cache_data(ttl=60)
def fetch_global_metrics() -> Dict[str, Any]:
    """Fetch global (lifetime) metrics from backend."""
    try:
        from streamlit_app.src.api.client import fetch_portfolio_daily

        # Fetch only "FULL portfolio" data to avoid getting individual ticker data
        df = fetch_portfolio_daily(ticker="FULL")
        df = prepare_portfolio_dataframe(df)

        if df.empty:
            return {}

        latest = df.iloc[-1]

        return {
            "portfolio_value": latest.get("Current Value (€)", 0),
            "total_invested": latest.get("Total Cost (€)", 0),
            "unrealized_gains": latest.get("Current Money Weighted Return (€)", 0),
            "unrealized_gains_pct": latest.get("Current Performance (%)", 0),
            "transaction_costs": latest.get("Transaction Costs (€)", 0),
            "latest_row": latest,
        }
    except Exception as e:
        handle_api_error(e, "Failed to load global metrics")
        return {}


@st.cache_data(ttl=300)
def fetch_period_metrics(start_date: str, end_date: str) -> Dict[str, Any]:
    """Fetch period-dependent metrics from backend."""
    try:
        from streamlit_app.src.api.client import fetch_portfolio_daily

        # Fetch only "FULL portfolio" data to avoid mixing individual tickers
        df = fetch_portfolio_daily(ticker="FULL", start_date=start_date, end_date=end_date)
        df = prepare_portfolio_dataframe(df)

        if df.empty:
            return {
                "period_return_pct": 0,
                "period_performance_pct": 0,
                "annualized_return_pct": 0,
                "realized_gains": 0,
                "best_day_pct": None,
                "worst_day_pct": None,
                "portfolio_value": 0,
                "total_cost": 0,
            }

        start_row = df.iloc[0]
        end_row = df.iloc[-1]

        start_cost = start_row.get("Total Cost (€)", 0)
        end_cost = end_row.get("Total Cost (€)", 0)
        start_value = start_row.get("Current Value (€)", 0)
        end_value = end_row.get("Current Value (€)", 0)

        # Calculate realized gains change during period
        realized_gains = round(end_row.get("Realized Return (€)", 0) - start_row.get("Realized Return (€)", 0), 2)

        # Calculate unrealized gains change during period
        unrealized_gains_start = start_row.get("Current Money Weighted Return (€)", 0)
        unrealized_gains_end = end_row.get("Current Money Weighted Return (€)", 0)

        # For "All time" periods, use the current unrealized gains value (not the change)
        # For other periods, use the change in unrealized gains
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days_in_period = max(1, (end_dt - start_dt).days)

        is_all_time = (end_dt - start_dt).days >= 36000  # Approximately 100 years
        if is_all_time:
            unrealized_gains_period = round(unrealized_gains_end, 2)
        else:
            unrealized_gains_period = round(unrealized_gains_end - unrealized_gains_start, 2)

        # Period Return = Realized Gains + Unrealized Gains (this ensures the relationship holds)
        period_return_euro = realized_gains + unrealized_gains_period

        # Calculate period return percentage with correct denominator
        if start_cost != 0:
            period_return_pct = round((period_return_euro / start_cost) * 100, 2)
        else:
            period_return_pct = 0

        # Calculate period performance percentage (considering capital flows)
        # For "All time" periods, always use total_invested_amount (total capital ever invested)
        # For shorter periods, use start_value (capital at period start)
        end_row_total_cost = end_row.get("Total Cost (€)", 0)

        if start_value > 0:
            # Use start value as denominator (performance from the capital base at period start)
            period_performance_pct = round((period_return_euro / start_value) * 100, 2)
        else:
            period_performance_pct = 0

        if days_in_period >= 365:
            annualized_return = round(period_return_pct, 2)
        elif period_return_pct != 0:
            annualized_return = round(((1 + period_return_pct / 100) ** (365 / days_in_period) - 1) * 100, 2)
        else:
            annualized_return = 0

        # Calculate unrealized gains percentage for period
        if start_value > 0:
            unrealized_gains_pct_period = round((unrealized_gains_period / start_value) * 100, 2)
        else:
            unrealized_gains_pct_period = 0
        # TODO this should be done at backend level
        return {
            "period_return_pct": period_return_pct,
            "period_return_euro": round(period_return_euro, 2),
            "period_performance_pct": period_performance_pct,
            "annualized_return_pct": annualized_return,
            "realized_gains": realized_gains,
            "unrealized_gains": unrealized_gains_period,
            "unrealized_gains_pct": unrealized_gains_pct_period,
            "best_day_pct": None,
            "worst_day_pct": None,
            "portfolio_value": end_row.get("Current Value (€)", 0),
            "total_cost": end_row.get("Total Cost (€)", 0),
            "total_invested_amount": end_row_total_cost,
            "df": df,
        }
    except Exception as e:
        handle_api_error(e, "Failed to load period metrics")
        return {}


@st.cache_data(ttl=300)
def fetch_ytd_metrics() -> Dict[str, Any]:
    """Fetch Year-to-Date metrics."""
    try:
        from streamlit_app.src.api.client import fetch_portfolio_daily

        today = datetime.now().date()
        ytd_start = f"{today.year}-01-01"
        ytd_end = today.strftime("%Y-%m-%d")

        # Fetch only "FULL portfolio" data to avoid mixing individual tickers
        df = fetch_portfolio_daily(ticker="FULL", start_date=ytd_start, end_date=ytd_end)
        df = prepare_portfolio_dataframe(df)

        if df.empty:
            return {"ytd_return_pct": 0}

        start_row = df.iloc[0]
        end_row = df.iloc[-1]

        start_cost = start_row.get("Total Cost (€)", 0)
        end_cost = end_row.get("Total Cost (€)", 0)
        start_value = start_row.get("Current Value (€)", 0)

        net_return_start = start_row.get('Net Return (€)', 0)
        net_return_end = end_row.get('Net Return (€)', 0)
        period_return_euro = net_return_end - net_return_start

        if start_cost != 0:
            ytd_return_pct = round((period_return_euro / start_cost) * 100, 2)
        else:
            ytd_return_pct = 0

        # Calculate YTD performance percentage (considering capital flows)
        # Prefer start_value when available, use capital flows only if start_value is 0
        capital_invested_ytd = end_cost - start_cost
        if start_value > 0:
            ytd_performance_pct = round((period_return_euro / start_value) * 100, 2)
        elif abs(capital_invested_ytd) >= 10:
            ytd_performance_pct = round((period_return_euro / abs(capital_invested_ytd)) * 100, 2)
        else:
            ytd_performance_pct = 0

        return {"ytd_return_pct": ytd_return_pct, "ytd_performance_pct": ytd_performance_pct}
    except Exception as e:
        handle_api_error(e, "Failed to load YTD metrics")
        return {"ytd_return_pct": 0}


def get_period_dates(period_key: str) -> Tuple[str, str]:
    """Convert period key to start_date and end_date strings."""
    today = datetime.now().date()

    if period_key == "YTD":
        start_date = datetime(today.year, 1, 1).date()
    elif period_key == "All time":
        start_date = today - timedelta(days=36500)
    elif period_key == "Last year":
        start_date = today - timedelta(days=365)
    elif period_key == "Last month":
        start_date = today - timedelta(days=30)
    else:
        days_offset = PERIOD_PRESETS[period_key][0]
        start_date = today + timedelta(days=days_offset)

    return start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


# ============================================================================
# CUSTOM STYLING
# ============================================================================

def inject_custom_css():
    """Inject custom CSS for beautiful card layout."""
    custom_css = """
    <style>
    /* Segmented Control - Make it bigger */
    [data-testid="stSegmentedControl"] {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }
    
    [data-testid="stSegmentedControl"] button {
        font-size: 1.1rem;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
    }
    
    /* Metric Cards Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        transition: all 0.3s ease;
        border-left: 4px solid #0066cc;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.12);
    }
    
    .metric-card.positive {
        border-left-color: #10b981;
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
    }
    
    .metric-card.negative {
        border-left-color: #ef4444;
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
    }
    
    .metric-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
    }
    
    .metric-icon {
        font-size: 1.5rem;
        line-height: 1;
    }
    
    .metric-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0.5rem 0;
    }
    
    .metric-context {
        font-size: 0.75rem;
        color: #999;
        margin-top: 0.5rem;
    }
    
    .metric-delta {
        font-size: 0.875rem;
        color: #666;
        margin-top: 0.5rem;
        font-weight: 500;
    }
    
    /* Period Selector */
    .period-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    .period-selector h2 {
        margin-top: 0;
        color: white;
    }
    
    /* Holdings Section */
    .holdings-section {
        background: #f9fafb;
        padding: 2rem;
        border-radius: 12px;
        margin-top: 2rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .metrics-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
        
        .period-selector {
            padding: 1rem;
        }
        
        [data-testid="stSegmentedControl"] button {
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
        }
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


# ============================================================================
# RENDERING FUNCTIONS
# ============================================================================

def render_header():
    """Render page header."""
    st.title("📊 Portfolio Metrics Dashboard")
    st.markdown(
        "Real-time portfolio performance tracking — "
        "select a period to see how your investments performed"
    )


def render_period_selector() -> str:
    """Render sticky period selector with segmented control buttons and custom date option."""

    st.markdown("### 📅 Select period:")

    selected_period = st.segmented_control(
        "Period:",
        options=list(PERIOD_PRESETS.keys()),
        default="All time",
        selection_mode="single",
        key="period_selector",
        label_visibility="collapsed"
    )

    # Show selected period dates below the selector using metric widgets
    start_date_str, end_date_str = get_period_dates(selected_period)
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    col = st.container()
    with col:
        subcol1, subcol2, _, _ = st.columns(4)
        with subcol1:
            st.metric("From", start_date.strftime('%d %b %Y'))
        with subcol2:
            st.metric("To", end_date.strftime('%d %b %Y'))

    return selected_period


def render_metrics_grid(global_metrics: Dict, period_metrics: Dict, ytd_metrics: Dict):
    """Render the 3×3 grid of metric cards."""

    # ROW 1: CURRENT STATE
    col1, col2, col3 = st.columns(3)

    with col1:
        html = render_metric_card(
            icon="🤑",
            title="Portfolio Value",
            value=format_currency(global_metrics.get("portfolio_value", 0)),
            context="Current as of Today",
            delta_color=False
        )
        st.markdown(html, unsafe_allow_html=True)

    with col2:
        period_return_euro = period_metrics.get("period_return_euro", 0)
        period_performance_pct = period_metrics.get("period_performance_pct", 0)

        html = render_metric_card(
            icon="📈",
            title="Period Return",
            value=format_currency(period_return_euro),
            context="Return within the selected period",
            color_value=period_performance_pct
        )
        st.markdown(html, unsafe_allow_html=True)

    with col3:
        period_performance_pct = period_metrics.get("period_performance_pct", 0)

        html = render_metric_card(
            icon="🎯",
            title="Performance %",
            value=format_percentage(period_performance_pct),
            context="Performance within the selected period",
            color_value=period_performance_pct
        )
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("")  # Spacing

    # ROW 2: PERIOD SPECIFICS
    col1, col2, col3 = st.columns(3)

    with col1:
        unrealized_gains = period_metrics.get("unrealized_gains", 0)

        html = render_metric_card(
            icon="💰",
            title="Unrealized Gains",
            value=format_currency(unrealized_gains),
            context="From holdings within the selected period",
            color_value=unrealized_gains
        )
        st.markdown(html, unsafe_allow_html=True)

    with col2:
        realized_gains = period_metrics.get("realized_gains", 0)

        html = render_metric_card(
            icon="💸",
            title="Realized Gains",
            value=format_currency(realized_gains),
            context="From sales within the selected period",
            color_value=realized_gains
        )
        st.markdown(html, unsafe_allow_html=True)

    with col3:
        html = render_metric_card(
            icon="📊",
            title="YTD Return %",
            value=format_percentage(ytd_metrics.get("ytd_return_pct", 0)),
            context="From Jan 1 to Today",
            color_value=ytd_metrics.get("ytd_return_pct", 0)
        )
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("")  # Spacing


def render_holdings_section(global_metrics: Dict, period_metrics: Dict):
    """Render holdings and capital flows section."""
    st.markdown("---")
    st.markdown("## 📋 Holdings & Capital Flows")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏢 Portfolio Composition")
        latest_row = global_metrics.get("latest_row")

        if latest_row is not None:
            st.metric("Total Value", format_currency(latest_row.get("Current Value (€)", 0)))
            st.metric("Total Invested", format_currency(latest_row.get("Total Cost (€)", 0)))
            st.metric("Unrealized Gains", format_currency(latest_row.get("Current Money Weighted Return (€)", 0)))

        st.info("📊 Detailed stock-by-stock breakdown coming soon")

    with col2:
        st.markdown("### 💳 Capital Flows")

        col2a, col2b = st.columns(2)
        with col2a:
            st.metric(
                "Total Invested (Lifetime)",
                format_currency(global_metrics.get("total_invested", 0))
            )
            st.metric(
                "Transaction Costs",
                format_currency(global_metrics.get("transaction_costs", 0))
            )
        with col2b:
            st.metric(
                "Realized Gains (Period)",
                format_currency(period_metrics.get("realized_gains", 0))
            )
            annualized = period_metrics.get("annualized_return_pct", 0)
            st.metric(
                "Annualized Return %",
                format_percentage(annualized)
            )


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application logic."""
    # Inject custom CSS
    inject_custom_css()

    # Check backend
    if not is_backend_alive():
        st.error("❌ Backend API is not reachable. Please ensure the backend is running.")
        st.stop()

    # Check data
    if not portfolio_data_exists():
        st.warning("⚠️ No portfolio data found. Please go to Dashboard and upload your transactions file.")
        st.stop()

    # Render header
    render_header()

    # Period selector (sticky at top)
    st.markdown("---")
    selected_period = render_period_selector()
    st.markdown("---")

    # Fetch all metrics
    global_metrics = fetch_global_metrics()
    start_date, end_date = get_period_dates(selected_period)
    period_metrics = fetch_period_metrics(start_date, end_date)
    ytd_metrics = fetch_ytd_metrics()

    # Render 3×3 grid
    render_metrics_grid(global_metrics, period_metrics, ytd_metrics)

    # Render holdings section
    render_holdings_section(global_metrics, period_metrics)

    # Footer
    st.markdown("---")
    st.caption(
        "💡 **Tip:** Changes are automatically cached for 5 minutes. "
        "Refresh data with the backend if needed."
    )


if __name__ == "__main__":
    main()
