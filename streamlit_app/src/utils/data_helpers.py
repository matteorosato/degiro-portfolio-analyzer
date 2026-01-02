"""
Data manipulation helper functions.

Provides utility functions for common data transformations.
"""

from typing import Optional, List
import pandas as pd
from config import UIConstants


def remove_flat_line(arr: List[float]) -> Optional[List[float]]:
    """
    Remove flat line from array (all values are the same).
    
    Used to hide trend charts when there's no variation in data.
    
    Args:
        arr: List of numeric values
    
    Returns:
        None if array is empty or flat, otherwise the original array
    """
    if len(arr) == 0:
        return None
    if min(arr) == max(arr):
        return None
    return arr


def filter_full_portfolio(df: pd.DataFrame, product_column: str = "Product") -> pd.DataFrame:
    """
    Filter out Full Portfolio entry from DataFrame.
    
    Args:
        df: DataFrame to filter
        product_column: Name of the column containing product names
    
    Returns:
        Filtered DataFrame without Full Portfolio entry
    """
    return df[df[product_column] != UIConstants.FULL_PORTFOLIO_NAME]
