"""
Chart creation helpers for Plotly visualizations.

Provides reusable functions for creating consistent charts.
"""

from typing import Dict, Optional
import pandas as pd
import plotly.express as px
from config import UIConstants, ColorScheme


def create_line_chart_by_type(
    df: pd.DataFrame,
    metric: str,
    date_column: str = "End Date"
) -> px.line:
    """
    Create a line chart showing metric over time by Product Type.
    
    Args:
        df: DataFrame with End Date, Product Type, and metric columns
        metric: The column name to plot on Y-axis
        date_column: Name of the date column (default: End Date)
    
    Returns:
        Plotly Figure object
    """
    fig = px.line()  # Empty figure
    
    # Get color mapping
    product_type_colors = ColorScheme.PRODUCT_TYPE_COLORS
    
    # Loop over each product type and add a line
    for product_type in df["Product Type"].unique():
        product_data = df[df["Product Type"] == product_type]
        
        fig.add_scatter(
            x=product_data[date_column],
            y=product_data[metric],
            mode="lines",
            name=product_type,
            line=dict(
                shape='spline',
                smoothing=UIConstants.PLOTLY_SMOOTH_FACTOR,
                color=product_type_colors.get(product_type, "#888")
            )
        )
    
    # Add dashed line at y=0 if there are negative values
    if (df[metric] < 0).any():
        fig.add_shape(
            type="line",
            x0=df[date_column].min(),
            x1=df[date_column].max(),
            y0=0,
            y1=0,
            line=dict(color="black", width=1, dash="dash"),
            xref="x",
            yref="y"
        )
    
    # Update layout
    fig.update_layout(
        width=UIConstants.PLOTLY_LINE_CHART_WIDTH,
        height=UIConstants.PLOTLY_LINE_CHART_HEIGHT,
        margin=dict(l=0, r=0, t=50, b=50),
        showlegend=True,
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", yanchor="bottom")
    )
    
    return fig


def create_split_chart(
    df: pd.DataFrame,
    metric: str,
    date_column: str = "End Date"
) -> px.pie or px.bar:
    """
    Create either a pie chart or bar chart based on metric values.
    
    Uses pie chart for all positive values, bar chart if any negative values.
    
    Args:
        df: DataFrame with latest date data and metric column
        metric: The column name to visualize
        date_column: Name of the date column
    
    Returns:
        Plotly Figure object (pie or bar)
    """
    # Get color mapping
    product_type_colors = ColorScheme.PRODUCT_TYPE_COLORS
    
    # Check for negative values
    if (df[metric] < 0).any():
        # Use bar chart if any value is negative
        fig = px.bar(
            df,
            x="Product Type",
            y=metric,
            color="Product Type",
            color_discrete_map=product_type_colors,
            text=metric
        )
        fig.update_layout(showlegend=False)
        fig.update_layout(
            bargap=UIConstants.PLOTLY_BAR_GAP,
            height=UIConstants.PLOTLY_SPLIT_CHART_HEIGHT,
            margin=dict(l=0, r=0, t=25, b=0)
        )
    else:
        # Use pie chart if all values are positive
        fig = px.pie(
            df,
            names="Product Type",
            values=metric,
            hole=0.5,
            color="Product Type",
            color_discrete_map=product_type_colors
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=False)
        fig.update_layout(
            height=UIConstants.PLOTLY_SPLIT_CHART_HEIGHT,
            margin=dict(l=0, r=0, t=25, b=0)
        )
    
    return fig
