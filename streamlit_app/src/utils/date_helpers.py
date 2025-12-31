"""Date range calculation utilities.

This module provides reusable functions for date range calculations
used across multiple pages for filtering portfolio data.
"""

from datetime import datetime, timedelta
from typing import Tuple, Dict


def calculate_date_mapping(max_date: datetime, min_date: datetime) -> Dict[str, Tuple[int, int]]:
    """Calculate date range mapping for different time periods.
    
    Args:
        max_date: Maximum date (usually most recent portfolio date)
        min_date: Minimum date (usually first transaction date)
        
    Returns:
        Dictionary mapping period names to (days_back, days_forward) tuples
    """
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
    
    return {
        "1Y": (365, 0),
        "3M": (90, 0),
        "1M": (30, 0),
        "1W": (7, 0),
        "1D": (1, 0),
        "YTD": (days_since_year_start, 0),
        "Last year": (days_in_last_year + days_since_year_start, days_since_year_start + 1),
        "Last month": (days_in_last_month + days_since_month_start, days_since_month_start + 1),
        "All time": ((max_date - min_date).days, 0)
    }


def get_date_range(
    selection: str,
    max_date: datetime,
    min_date: datetime
) -> Tuple[datetime, datetime]:
    """Get start and end dates for a given period selection.
    
    Args:
        selection: Period selection (1Y, 3M, 1M, 1W, YTD, Last year, Last month, All time)
        max_date: Maximum date (usually most recent portfolio date)
        min_date: Minimum date (usually first transaction date)
        
    Returns:
        Tuple of (start_date, end_date)
    """
    date_mapping = calculate_date_mapping(max_date, min_date)
    days_back, days_forward = date_mapping.get(selection, (0, 0))
    
    start_date = max_date - timedelta(days=days_back)
    end_date = max_date - timedelta(days=days_forward)
    
    return start_date, end_date
