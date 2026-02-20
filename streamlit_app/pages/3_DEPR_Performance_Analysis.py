"""
Performance Analysis Page - Section 1: Comprehensive Performance Analysis

This page provides detailed portfolio performance analysis including:
- Portfolio value changes over selected period
- Return metrics and gains breakdown
- Comparison with historical total portfolio performance
- Capital flows analysis
- Interactive visualizations
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import requests
from streamlit_app.src.api import client

# Page configuration
st.set_page_config(
    page_title="Performance Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"€ {value:,.2f}"

def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:+.2f}%" if value else "0.00%"

def get_color_for_value(value: float) -> str:
    """Get color based on positive/negative value."""
    return "green" if value >= 0 else "red"

def transform_api_response(api_response: dict, start_date: datetime, end_date: datetime) -> dict:
    """Transform API response to metrics format expected by render functions.
    
    Args:
        api_response: Response from calculate_portfolio_range endpoint
        start_date: Start date of period
        end_date: End date of period
        
    Returns:
        Dictionary with metrics in expected format
    """
    data = api_response.get("data", {})
    stocks_data = data.get("all_stocks_mwr", {})
    
    period_days = (end_date - start_date).days
    
    # Calculate returns
    return_euro_period = stocks_data.get("unrealized_return", 0)
    total_invested = stocks_data.get("total_invested_amount", 0)
    
    # Period return percentage: return / capital invested
    return_percent_period = 0
    if abs(total_invested) >= 10:
        return_percent_period = (return_euro_period / abs(total_invested)) * 100
    
    # Annualized return: scale to full year
    annualized_return = 0
    if period_days > 0:
        annualized_return = (return_percent_period * 365) / period_days
    
    # Total all-time return percentage
    total_net_return = stocks_data.get("net_return", 0)
    total_invested_all_time = stocks_data.get("total_invested_amount", 0)
    total_return_percent = 0
    if abs(total_invested_all_time) >= 10:
        total_return_percent = (total_net_return / abs(total_invested_all_time)) * 100
    
    return {
        # Portfolio values
        "value_start_period": 0,  # Not available from API
        "value_end_period": stocks_data.get("current_value", 0),
        "period_days": period_days,
        "total_days": 365,  # Default to 1 year - actual start date not available from API
        
        # Capital flows
        "net_capital_invested": stocks_data.get("total_invested_amount", 0),
        "dividends_period": 0,  # Not tracked in current implementation
        "commissions_period": 0,  # Not tracked in current implementation
        
        # Returns
        "return_euro_period": return_euro_period,
        "return_percent_period": return_percent_period,
        "annualized_return": annualized_return,
        "total_return_percent": total_return_percent,
        
        # Gains breakdown
        "realized_gains_period": stocks_data.get("total_sales_proceeds", 0),
        "unrealized_gains": stocks_data.get("unrealized_return", 0),
        
        # Sales metrics
        "total_sales_proceeds": stocks_data.get("total_sales_proceeds", 0),
        "total_sales_quantity": stocks_data.get("total_sales_quantity", 0),
        "avg_sale_price": stocks_data.get("avg_sale_price", 0),
        "total_bought_quantity": stocks_data.get("total_bought_quantity", 0),
        "avg_buy_price": stocks_data.get("avg_buy_price", 0),
    }

def render_header() -> None:
    """Render page header."""
    st.title("📊 Performance Analysis")
    st.markdown(
        "Comprehensive portfolio performance analysis for selected period, including returns, "
        "capital flows, and comparison with historical performance."
    )

def render_period_selector() -> tuple:
    """Render period selection in sidebar.
    
    Returns:
        Tuple of (start_date, end_date) as datetime objects
    """
    st.sidebar.subheader("📅 Period Selection")
    
    # Preset period options
    period_option = st.sidebar.radio(
        "Select period",
        ["Last Month", "Last 3 Months", "Last 6 Months", "Year to Date", "All Time", "Custom Range"],
        index=2
    )
    
    end_date = datetime.now()
    
    if period_option == "Last Month":
        start_date = end_date - timedelta(days=30)
    elif period_option == "Last 3 Months":
        start_date = end_date - timedelta(days=90)
    elif period_option == "Last 6 Months":
        start_date = end_date - timedelta(days=180)
    elif period_option == "Year to Date":
        start_date = datetime(end_date.year, 1, 1)
    elif period_option == "All Time":
        start_date = datetime(2020, 1, 1)
    else:  # Custom Range
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Start date", value=end_date - timedelta(days=90))
        with col2:
            end_date_sel = st.date_input("End date", value=end_date)
            end_date = datetime.combine(end_date_sel, datetime.max.time())
        start_date = datetime.combine(start_date, datetime.min.time())
    
    return start_date, end_date

def render_performance_section(metrics: dict) -> None:
    """Render the main performance analysis section with 3 tabs.
    
    Args:
        metrics: Dictionary containing period metrics from API
    """
    tab1, tab2, tab3 = st.tabs(["💰 Portfolio Value", "📈 Returns", "📊 Comparison"])
    
    with tab1:
        render_value_tab(metrics)
    
    with tab2:
        render_returns_tab(metrics)
    
    with tab3:
        render_comparison_tab(metrics)

def render_value_tab(metrics: dict) -> None:
    """Render portfolio value tab.
    
    Args:
        metrics: Dictionary containing period metrics
    """
    st.markdown("#### Portfolio Values During Period")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Starting Value",
            format_currency(metrics['value_start_period'])
        )
    
    with col2:
        st.metric(
            "Ending Value",
            format_currency(metrics['value_end_period'])
        )
    
    with col3:
        delta_value = metrics['value_end_period'] - metrics['value_start_period']
        st.metric(
            "Value Change",
            format_currency(delta_value),
            delta=format_currency(delta_value),
            delta_color="inverse" if delta_value < 0 else "normal"
        )
    
    with col4:
        st.metric(
            "Period Duration",
            f"{metrics['period_days']} days"
        )
    
    st.divider()
    
    st.markdown("#### Capital Flows")
    
    flow_col1, flow_col2, flow_col3 = st.columns(3)
    
    with flow_col1:
        st.metric(
            "Net Capital Invested",
            format_currency(metrics['net_capital_invested']),
            delta="Difference in investment base"
        )
    
    with flow_col2:
        st.metric(
            "Dividends Received",
            format_currency(metrics['dividends_period']),
            delta="Income generated"
        )
    
    with flow_col3:
        st.metric(
            "Transaction Fees",
            format_currency(metrics['commissions_period']),
            delta="Total costs incurred"
        )
    
    st.info(
        f"📌 During this period, you invested **{format_currency(metrics['net_capital_invested'])}** in net capital, "
        f"received **{format_currency(metrics['dividends_period'])}** in dividends, and paid "
        f"**{format_currency(metrics['commissions_period'])}** in transaction fees."
    )

def render_returns_tab(metrics: dict) -> None:
    """Render returns tab with breakdown and visualization.
    
    Args:
        metrics: Dictionary containing period metrics
    """
    st.markdown("#### Period Returns Analysis")
    
    ret_col1, ret_col2, ret_col3 = st.columns(3)
    
    with ret_col1:
        delta_color = "inverse" if metrics['return_euro_period'] < 0 else "normal"
        st.metric(
            "Total Gain/Loss",
            format_currency(metrics['return_euro_period']),
            delta=format_percentage(metrics['return_percent_period']),
            delta_color=delta_color
        )
    
    with ret_col2:
        st.metric(
            "Return Percentage",
            format_percentage(metrics['return_percent_period']),
            delta="On capital invested"
        )
    
    with ret_col3:
        st.metric(
            "Annualized Return",
            format_percentage(metrics['annualized_return']),
            delta="Extrapolated to full year"
        )
    
    st.divider()
    
    st.markdown("#### Gains Breakdown")
    
    break_col1, break_col2 = st.columns(2)
    
    with break_col1:
        st.markdown("**Realized Gains** (from closed positions)")
        color_real = "🟢" if metrics['realized_gains_period'] >= 0 else "🔴"
        st.metric("", f"{color_real} {format_currency(metrics['realized_gains_period'])}")
    
    with break_col2:
        st.markdown("**Unrealized Gains** (from open positions)")
        color_unreal = "🟢" if metrics['unrealized_gains'] >= 0 else "🔴"
        st.metric("", f"{color_unreal} {format_currency(metrics['unrealized_gains'])}")
    
    st.markdown("**Return Composition**")
    
    breakdown_data = {
        'Realized': metrics['realized_gains_period'],
        'Unrealized': metrics['unrealized_gains'],
        'Dividends': metrics['dividends_period'],
        'Fees': -metrics['commissions_period']
    }
    
    fig = px.bar(
        x=list(breakdown_data.keys()),
        y=list(breakdown_data.values()),
        labels={'x': 'Component', 'y': 'Amount (€)'},
        color=['green' if v >= 0 else 'red' for v in breakdown_data.values()],
        title='Return Composition Breakdown',
        text=[format_currency(v) for v in breakdown_data.values()]
    )
    fig.update_layout(
        showlegend=False,
        height=400,
        hovermode='x unified',
        xaxis_title="Component",
        yaxis_title="Amount (€)"
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    st.plotly_chart(fig, use_container_width=True)

def render_comparison_tab(metrics: dict) -> None:
    """Render comparison with historical performance tab.
    
    Args:
        metrics: Dictionary containing period metrics
    """
    st.markdown("#### Performance Comparison with Historical Data")
    
    comp_col1, comp_col2, comp_col3 = st.columns(3)
    
    with comp_col1:
        st.markdown("**Period Return**")
        st.metric("", format_percentage(metrics['return_percent_period']))
        st.caption("For selected period")
    
    with comp_col2:
        st.markdown("**Historical Total Return**")
        st.metric("", format_percentage(metrics['total_return_percent']))
        st.caption("Since first transaction")
    
    with comp_col3:
        st.markdown("**Difference**")
        diff = metrics['return_percent_period'] - metrics['total_return_percent']
        color = "normal" if diff >= 0 else "inverse"
        st.metric("", format_percentage(diff), delta_color=color)
        st.caption("Above/below average")
    
    st.divider()
    
    st.markdown("#### Timeline Analysis")
    
    time_col1, time_col2 = st.columns(2)
    
    with time_col1:
        st.markdown("**Annualized Return**")
        st.metric("", format_percentage(metrics['annualized_return']))
        st.caption("Projected annual return")
    
    with time_col2:
        st.markdown("**Period Duration**")
        st.metric("", f"{metrics['period_days']} days")
        pct_time = (metrics['period_days'] / metrics['total_days'] * 100) if metrics['total_days'] > 0 else 0
        st.caption(f"{pct_time:.1f}% of total portfolio time")
    
    st.divider()
    
    st.markdown("### 🔍 Performance Insights")
    
    # Performance analysis insights
    if metrics['return_percent_period'] > metrics['total_return_percent']:
        st.success(
            f"✅ **Excellent Performance!** This period returned **{metrics['return_percent_period']:.2f}%**, "
            f"exceeding the historical average of **{metrics['total_return_percent']:.2f}%** "
            f"(difference: +{metrics['return_percent_period'] - metrics['total_return_percent']:.2f}%)"
        )
    elif abs(metrics['return_percent_period'] - metrics['total_return_percent']) < 1:
        st.info(
            f"➡️ **In Line with Average**: Period return of **{metrics['return_percent_period']:.2f}%** "
            f"matches historical average of **{metrics['total_return_percent']:.2f}%**"
        )
    else:
        st.warning(
            f"⚠️ **Below Average Performance**: This period returned **{metrics['return_percent_period']:.2f}%**, "
            f"below the historical average of **{metrics['total_return_percent']:.2f}%** "
            f"(difference: {metrics['return_percent_period'] - metrics['total_return_percent']:.2f}%)"
        )
    
    # Annualized return projection
    if metrics['annualized_return'] > 15:
        st.info(
            f"📈 **Strong Performance!** At this rate, you would gain **{metrics['annualized_return']:.2f}%** annually."
        )
    elif metrics['annualized_return'] > 0:
        st.info(
            f"📊 **Positive Annualized Return**: **{metrics['annualized_return']:.2f}%** per year based on this period."
        )
    else:
        st.warning(
            f"📉 **Negative Trend**: Annualized return is **{metrics['annualized_return']:.2f}%**. Monitor your positions."
        )
    
    # Capital contribution analysis
    if metrics['net_capital_invested'] > 0:
        st.info(
            f"💰 **Capital Contribution**: You invested **{format_currency(metrics['net_capital_invested'])}** "
            f"in net capital. Your return on this investment is **{metrics['return_percent_period']:.2f}%**."
        )
    
    # Realized vs Unrealized gains
    if metrics['realized_gains_period'] > metrics['unrealized_gains']:
        st.success(
            f"✓ **Lock in Gains**: You have realized more gains than unrealized "
            f"(Realized: {format_currency(metrics['realized_gains_period'])})"
        )
    elif metrics['unrealized_gains'] > 0:
        st.info(
            f"📈 **Growth Potential**: Most of your gains are from open positions "
            f"(Unrealized: {format_currency(metrics['unrealized_gains'])})"
        )

def main():
    """Main page logic."""
    render_header()
    
    # Get date range from sidebar
    start_date, end_date = render_period_selector()
    
    # Display selected period
    st.sidebar.success(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )
    
    # Fetch metrics from API
    try:
        with st.spinner("📊 Calculating period metrics..."):
            api_response = client.calculate_portfolio_range(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            # Transform API response to format expected by render functions
            metrics = transform_api_response(api_response, start_date, end_date)
        
        # Render performance analysis
        render_performance_section(metrics)
        
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ **Connection Error**: Cannot connect to backend API. "
            "Make sure the backend is running on http://localhost:8000"
        )
    except Exception as e:
        st.error(f"❌ **Error Loading Metrics**: {str(e)}")
        st.info("Please ensure:")
        st.info("• Backend API is running")
        st.info("• Portfolio calculation has been completed")
        st.info("• Selected date range has transaction data")

if __name__ == "__main__":
    main()
