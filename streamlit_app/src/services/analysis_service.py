"""
Analysis service for portfolio analytics.

Provides business logic for portfolio analysis calculations.
"""

from datetime import timedelta
from typing import Dict, Tuple, List
import pandas as pd
from config import UIConstants


def find_valid_dates(
    all_dates: List[pd.Timestamp],
    selected_date: pd.Timestamp
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Find the two most recent valid dates for daily change calculation.
    
    Args:
        all_dates: List of all available dates (sorted)
        selected_date: User-selected date
    
    Returns:
        Tuple of (date_1, date_0) where date_1 is most recent and date_0 is previous
    """
    # Find dates before or equal to selected date
    valid_dates = [d for d in all_dates if d <= selected_date]
    
    if not valid_dates:
        # If no date before selected_date, use the first date
        date_1 = all_dates[0]
        date_0 = all_dates[0]
    else:
        date_1 = valid_dates[-1]  # Most recent valid date
        date_1_idx = all_dates.index(date_1)
        date_0 = all_dates[date_1_idx - 1] if date_1_idx > 0 else date_1
    
    return date_1, date_0


def calculate_daily_change(
    df: pd.DataFrame,
    date_1: pd.Timestamp,
    date_0: pd.Timestamp
) -> Dict[str, float]:
    """
    Calculate daily change in portfolio value.
    
    Args:
        df: Portfolio DataFrame
        date_1: Most recent date
        date_0: Previous date
    
    Returns:
        Dictionary with daily change metrics
    """
    daily_value_start = df[df['End Date'] == date_0]['Current Value (€)'].sum()
    daily_value_end = df[df['End Date'] == date_1]['Current Value (€)'].sum()
    
    if daily_value_start != 0:
        daily_delta = round(daily_value_end - daily_value_start, 2)
        daily_delta_per = round((daily_delta / daily_value_start) * 100, 2)
    else:
        daily_delta = 0.0
        daily_delta_per = 0.0
    
    return {
        "current_value": daily_value_end,
        "daily_delta": daily_delta,
        "daily_delta_per": daily_delta_per
    }


def calculate_allocation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate current allocation percentage for each product.
    
    Args:
        df: Portfolio DataFrame for selected date
    
    Returns:
        DataFrame with 'Current Allocation %' column added
    """
    total_value = df['Current Value (€)'].sum()
    
    if total_value > 0:
        df["Current Allocation %"] = (df['Current Value (€)'] / total_value) * 100
    else:
        df["Current Allocation %"] = 0.0
    
    return df


def calculate_trend_data(
    df: pd.DataFrame,
    products: pd.Series,
    date_1: pd.Timestamp,
    days: int = UIConstants.TREND_DAYS
) -> pd.Series:
    """
    Calculate trend data for each product over the last N days.
    
    Args:
        df: Complete portfolio DataFrame
        products: Series of product names
        date_1: Most recent date
        days: Number of days for trend (default from UIConstants)
    
    Returns:
        Series with list of Net Performance (%) values for each product
    """
    date_start = date_1 - timedelta(days=days)
    
    def get_trend(product_name):
        trend_data = df[
            (df["Product"] == product_name) &
            (df["End Date"] >= date_start) &
            (df["End Date"] <= date_1)
        ]["Net Performance (%)"].tolist()
        return trend_data
    
    return products.apply(get_trend)


def prepare_display_dataframe(
    df: pd.DataFrame,
    date_1: pd.Timestamp,
    holdings_option: str
) -> pd.DataFrame:
    """
    Prepare DataFrame for display with all calculations applied.
    
    Args:
        df: Complete portfolio DataFrame
        date_1: Selected date
        holdings_option: "Current Holdings" or "All Holdings"
    
    Returns:
        Prepared DataFrame ready for display
    """
    # Filter for selected date
    selected_day_df = df[df['End Date'] == date_1].copy()
    
    # Filter based on holdings option
    if holdings_option == "Current Holdings":
        selected_day_df = selected_day_df[selected_day_df["Quantity"] != 0]
    
    # Select relevant columns
    display_df = selected_day_df[[
        'Product', 'Quantity', 'Current Value (€)',
        'Net Return (€)', 'Net Performance (%)', 'Total Cost (€)'
    ]].copy()
    
    # Calculate allocation
    display_df = calculate_allocation(display_df)
    
    # Calculate trend data
    display_df["Net Performance (%) - Trend"] = calculate_trend_data(
        df, display_df["Product"], date_1
    )
    
    # Sort by allocation and total cost
    display_df = display_df.sort_values(
        by=['Current Allocation %', 'Total Cost (€)'],
        ascending=[False, False]
    )
    
    # Reorder columns
    display_df = display_df[[
        'Product', 'Current Allocation %', 'Quantity', 'Current Value (€)',
        'Net Return (€)', 'Net Performance (%)', 'Net Performance (%) - Trend',
        'Total Cost (€)'
    ]]
    
    return display_df
