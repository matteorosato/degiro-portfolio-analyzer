"""
Ticker and ISIN mapping service.

Handles operations related to ticker lookup, mapping validation,
and mapping persistence.
"""

from typing import Dict, Tuple, Any, Optional
import requests
import pandas as pd


def search_ticker(
    query: str, preferred_exchanges: Optional[list] = None
) -> Tuple[str, str]:
    """
    Search for ticker symbol using Yahoo Finance API.
    
    Args:
        query: Product name or search query
        preferred_exchanges: List of preferred exchanges (e.g., ["ETR", "XETRA"])
    
    Returns:
        Tuple of (ticker_symbol, company_name) or ("", "") if not found
    """
    url = (
        f"https://query1.finance.yahoo.com/v1/finance/search?"
        f"q={query}&quotesCount=10"
        f"&newsCount=0&listsCount=0"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Referer": "https://finance.yahoo.com"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        quotes = data.get("quotes", [])
        
        if not quotes:
            return "", ""

        # Filter if preferred exchanges are given
        if preferred_exchanges:
            for exch in preferred_exchanges:
                for quote in quotes:
                    if quote.get("exchange") == exch and "symbol" in quote:
                        return quote["symbol"], quote.get("longname", "")

        # Fallback to first valid result
        for quote in quotes:
            if "symbol" in quote:
                return quote["symbol"], quote.get("longname", "")

    except Exception as e:
        print(f"Ticker search error for '{query}': {e}")
        return "", ""

    return "", ""


def build_mapping_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build ISIN mapping dictionary from DataFrame.
    
    Converts DataFrame rows to the format expected by the backend API.
    
    Args:
        df: DataFrame with columns [ISIN, Ticker, Exchange, Product Name (DeGiro), Display Name, Product Type]
    
    Returns:
        Dictionary with ISIN as keys and mapping metadata as values
    """
    mapping = {
        row['ISIN']: {
            "ticker": row.get("Ticker", ""),
            "degiro_name": row.get("Product Name (DeGiro)", ""),
            "display_name": row.get("Display Name", ""),
            "exchange": row.get("Exchange", ""),
            "product_type": row.get("Product Type", "")
        }
        for _, row in df.iterrows()
    }
    return mapping


def load_mapping_dict(mapping_dict: Dict[str, Any]) -> pd.DataFrame:
    """
    Load DataFrame from ISIN mapping dictionary.
    
    Converts backend mapping format to DataFrame for display and editing.
    
    Args:
        mapping_dict: Dictionary with ISIN codes as keys and mapping metadata as values
    
    Returns:
        DataFrame with columns [ISIN, Ticker, Exchange, Product Name (DeGiro), Display Name, Product Type]
    """
    return pd.DataFrame([
        {
            "ISIN": isin,
            "Ticker": data.get("ticker", ""),
            "Exchange": data.get("exchange", ""),
            "Product Name (DeGiro)": data.get("degiro_name", ""),
            "Display Name": data.get("display_name", ""),
            "Product Type": data.get("product_type", "")
        }
        for isin, data in mapping_dict.items()
    ])


def validate_mapping_dataframe(df: pd.DataFrame) -> bool:
    """
    Validate that DataFrame has required columns for mapping.
    
    Args:
        df: DataFrame to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_columns = [
        "ISIN",
        "Ticker",
        "Exchange",
        "Product Name (DeGiro)",
        "Display Name",
        "Product Type"
    ]
    return all(col in df.columns for col in required_columns)
