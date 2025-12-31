"""Data transformation utilities.

This module provides functions to transform raw API data into usable DataFrames
with proper column names, data types, and formatting.
"""

from typing import Dict, Any
import pandas as pd
from config import ColumnMappings


def prepare_portfolio_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare portfolio DataFrame with renamed columns and proper types.
    
    Args:
        df: Raw portfolio DataFrame from API
        
    Returns:
        Transformed DataFrame with renamed columns and datetime types
    """
    if df.empty:
        return df
    
    # Rename columns using mapping
    df = df.rename(columns=ColumnMappings.PORTFOLIO_RENAME)
    
    # Convert date columns to datetime
    if 'Start Date' in df.columns:
        df['Start Date'] = pd.to_datetime(df['Start Date'])
    if 'End Date' in df.columns:
        df['End Date'] = pd.to_datetime(df['End Date'])
    
    return df


def prepare_transactions_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare transactions DataFrame with proper types.
    
    Args:
        df: Raw transactions DataFrame from API
        
    Returns:
        Transformed DataFrame with datetime types
    """
    if df.empty:
        return df
    
    # Convert date column to datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    
    return df


def prepare_mapping_dataframe(mapping: Dict[str, Any]) -> pd.DataFrame:
    """Convert ISIN mapping dictionary to DataFrame.
    
    Args:
        mapping: ISIN mapping dictionary from API
        
    Returns:
        DataFrame with ISIN mapping data
    """
    df = pd.DataFrame([
        {
            "ISIN": isin,
            "Ticker": data.get("ticker", ""),
            "Exchange": data.get("exchange", ""),
            "Product Name (DeGiro)": data.get("degiro_name", ""),
            "Display Name": data.get("display_name", ""),
            "Product Type": data.get("product_type", "")
        }
        for isin, data in mapping.items()
    ])
    
    return df
