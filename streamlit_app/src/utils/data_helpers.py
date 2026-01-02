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
    if len(arr) == 0 or min(arr) == max(arr):
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


def enrich_with_product_type(df: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich portfolio DataFrame with Product Type from mapping.
    
    Args:
        df: Portfolio DataFrame with Ticker column
        mapping_df: Mapping DataFrame with Ticker and Product Type columns
    
    Returns:
        DataFrame with Product Type column added
    """
    return df.merge(
        mapping_df[['Ticker', 'Product Type']],
        left_on='Ticker',
        right_on='Ticker',
        how='left'
    )


def aggregate_by_product_type(df: pd.DataFrame, date_column: str = "End Date") -> pd.DataFrame:
    """
    Aggregate portfolio data by Product Type.
    
    Groups by End Date and Product Type, summing financial metrics.
    
    Args:
        df: DataFrame with Product Type and financial columns
        date_column: Name of the date column
    
    Returns:
        Aggregated DataFrame grouped by date and product type
    """
    return (
        df.groupby([date_column, "Product Type"])[
            ["Net Return (€)", "Total Cost (€)", "Current Value (€)"]
        ]
        .sum()
        .reset_index()
        .sort_values(by=[date_column, "Product Type"], ascending=False)
    )


def calculate_net_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Net Performance (%) from Net Return and Total Cost.
    
    Args:
        df: DataFrame with Net Return (€) and Total Cost (€) columns
    
    Returns:
        DataFrame with Net Performance (%) column added
    """
    df = df.copy()

    # Avoid division by zero
    total_cost_nonzero = df["Total Cost (€)"] != 0
    df.loc[total_cost_nonzero, "Net Performance (%)"] = (
            (df.loc[total_cost_nonzero, "Net Return (€)"] /
             df.loc[total_cost_nonzero, "Total Cost (€)"]) * 100
    )
    df.loc[~total_cost_nonzero, "Net Performance (%)"] = 0.0

    return df


def round_financial_columns(
        df: pd.DataFrame,
        decimal_places: int = 2,
        columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Round financial columns to specified decimal places.
    
    Args:
        df: DataFrame to round
        decimal_places: Number of decimal places
        columns: List of columns to round. If None, rounds all numeric columns
    
    Returns:
        DataFrame with rounded values
    """
    if columns is None:
        # Auto-detect financial columns
        columns = [
            "Net Return (€)",
            "Total Cost (€)",
            "Current Value (€)",
            "Net Performance (%)"
        ]
        # Only include columns that exist
        columns = [col for col in columns if col in df.columns]

    round_dict = {col: decimal_places for col in columns}
    return df.round(round_dict)
