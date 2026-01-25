"""Dashboard UI components.

This module contains reusable UI rendering functions for the Dashboard page.
Each function is responsible for a specific section of the dashboard.
"""

from datetime import datetime
from typing import Tuple, Optional

import pandas as pd
import plotly.express as px
import streamlit as st


def render_header() -> None:
    """Render dashboard header and title."""
    st.title("Portfolio Dashboard")


def render_product_selector(df: pd.DataFrame) -> Tuple[str, str]:
    """Render product selection dropdowns in the sidebar.
    
    Args:
        df: Portfolio dataframe with products
        
    Returns:
        Tuple of (selected_product, selected_compare_product)
    """
    # Sort product options
    product_options = sorted(df['Product'].unique().tolist())
    if "Full portfolio" in product_options:
        product_options.remove("Full portfolio")
        product_options.insert(0, "Full portfolio")

    # Set default index for "Full Portfolio"
    default_index = product_options.index("Full portfolio")
    selected_product = st.selectbox(
        "Select a Product", 
        options=product_options, 
        index=default_index,
        key="product_select"
    )

    # Dropdown to select another product for comparison
    compare_product_options = ["None"] + product_options
    selected_compare_product = st.selectbox(
        "Compare with another Product", 
        options=compare_product_options, 
        index=0,
        key="compare_product_select"
    )
    
    return selected_product, selected_compare_product


def render_metric_selector(df: pd.DataFrame) -> str:
    """Render performance metric selector in sidebar.
    
    Args:
        df: Portfolio dataframe
        
    Returns:
        Selected metric name
    """
    performance_metrics = [
        col for col in df.columns 
        if col not in ['Product', 'Ticker', 'Start Date', 'End Date']
    ]
    default_index_per = performance_metrics.index("Current Value (€)")
    selected_metric = st.selectbox(
        "Select a Performance Metric", 
        options=performance_metrics, 
        index=default_index_per,
        key="metric_select"
    )
    return selected_metric


def render_performance_chart(
    filtered_df: pd.DataFrame,
    selected_metric: str,
    selected_product: str,
    compare_product_df: Optional[pd.DataFrame] = None,
    selected_compare_product: Optional[str] = None,
    selected_start_date: Optional[datetime] = None,
    selected_end_date: Optional[datetime] = None
) -> None:
    """Render the main performance chart with optional comparison.
    
    Args:
        filtered_df: Filtered portfolio data for main product
        selected_metric: Metric to display
        selected_product: Name of main product
        compare_product_df: Optional comparison product data
        selected_compare_product: Optional comparison product name
        selected_start_date: Start date of selection
        selected_end_date: End date of selection
    """
    if filtered_df.empty:
        return
        
    st.subheader(f"{selected_metric} for {selected_product}")

    # Create plot
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
    if compare_product_df is not None and not compare_product_df.empty:
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


def render_portfolio_summary(
    filtered_df: pd.DataFrame,
    selected_start_date: datetime,
    selected_end_date: datetime,
    date_selection: str = "All time"
) -> None:
    """Render portfolio summary metrics section.
    
    Args:
        filtered_df: Filtered portfolio data
        selected_start_date: Period start date
        selected_end_date: Period end date
        date_selection: Selected date range option
    """
    # Format the date range for the title
    period_start_str = selected_start_date.strftime('%Y-%m-%d')
    period_end_str = selected_end_date.strftime('%Y-%m-%d')
    st.subheader(f"Portfolio Summary")
    st.caption(
        f"Period: {period_start_str} to {period_end_str} "
        f"({(selected_end_date - selected_start_date).days} days)"
    )

    # Calculate period metrics based on filtered data
    if len(filtered_df) > 0:
        period_start_value = filtered_df.iloc[0].get("Current Value (€)", 0)
        period_start_cost = filtered_df.iloc[0].get("Total Cost (€)", 0)
        period_end_value = filtered_df.iloc[-1].get("Current Value (€)", 0)
        period_end_cost = filtered_df.iloc[-1].get("Total Cost (€)", 0)
        
        # Use net return difference for accurate period calculation
        net_return_start = filtered_df.iloc[0].get('Net Return (€)', 0)
        net_return_end = filtered_df.iloc[-1].get('Net Return (€)', 0)
        period_return_euro = net_return_end - net_return_start
        
        # Calculate net cash flows during the period (investments/withdrawals)
        capital_invested_in_period = period_end_cost - period_start_cost
        
        # Calculate Period Performance % considering capital flows
        if abs(capital_invested_in_period) >= 10:
            # Significant capital flow in period - use capital invested as denominator
            period_performance_pct = (period_return_euro / abs(capital_invested_in_period)) * 100
        else:
            # No significant flows (HOLD period) - use start cost as denominator
            period_performance_pct = (period_return_euro / period_start_cost) * 100 if period_start_cost != 0 else 0
    else:
        period_end_value = 0
        period_return_euro = 0
        period_performance_pct = 0

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Portfolio Value",
            value=f"€ {period_end_value:,.2f}",
        )
    with col2:
        st.metric(
            label="Period Return",
            value=f"€ {period_return_euro:,.2f}"
        )
    with col3:
        performance_sign = "+" if period_performance_pct >= 0 else ""
        st.metric(
            label="Period Performance",
            value=f"{performance_sign}{period_performance_pct:.2f}%"
        )


def render_sales_metrics(
    total_sales_proceeds: float,
    total_sales_quantity: int,
    avg_sale_price: float,
    total_bought_quantity: int,
    avg_buy_price: float
) -> None:
    """Render sales and trading metrics section.
    
    Args:
        total_sales_proceeds: Total money received from stock sales
        total_sales_quantity: Total number of shares sold
        avg_sale_price: Average price per share sold
        total_bought_quantity: Total number of shares bought
        avg_buy_price: Average price per share bought
    """
    st.subheader("📊 Sales & Trading Metrics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Total Sales Proceeds",
            value=f"€ {total_sales_proceeds:,.2f}",
            help="Total money received from selling shares"
        )
    with col2:
        st.metric(
            label="Shares Sold",
            value=f"{total_sales_quantity:,}",
            help="Total number of shares sold"
        )
    with col3:
        st.metric(
            label="Avg Sale Price",
            value=f"€ {avg_sale_price:,.2f}",
            help="Average price per share when sold"
        )
    
    col4, col5 = st.columns(2)
    with col4:
        st.metric(
            label="Shares Bought",
            value=f"{total_bought_quantity:,}",
            help="Total number of shares purchased"
        )
    with col5:
        st.metric(
            label="Avg Buy Price",
            value=f"€ {avg_buy_price:,.2f}",
            help="Average price per share when purchased"
        )


def render_portfolio_composition(df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
    """Render portfolio composition table and pie chart.
    
    Args:
        df: Full portfolio dataframe
        filtered_df: Filtered portfolio data for selected product
    """
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

        # Display table
        st.dataframe(
            composition_display.style.format({
                'NAV': '€ {:,.2f}',
                'NAV %': '{:.2f}%'
            }),
            hide_index=True,
            use_container_width=True
        )

        # Create pie chart
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
