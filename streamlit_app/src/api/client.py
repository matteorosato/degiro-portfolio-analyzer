"""API client for backend communication.

This module provides reusable functions for all API interactions with the FastAPI backend.
All functions handle errors consistently and return appropriate data structures.
"""

from typing import Optional, Dict, Any
import pandas as pd
import requests
import streamlit as st
from config import FrontendConfig, APIEndpoints, UIConstants


def _make_api_request(
    method: str,
    endpoint: str,
    timeout: int = FrontendConfig.API_TIMEOUT,
    **kwargs
) -> requests.Response:
    """Make an API request with error handling.
    
    Args:
        method: HTTP method (GET, POST, DELETE)
        endpoint: API endpoint path
        timeout: Request timeout in seconds
        **kwargs: Additional arguments to pass to requests
        
    Returns:
        Response object
        
    Raises:
        requests.RequestException: On API errors
    """
    url = FrontendConfig.get_api_url(endpoint)
    response = requests.request(method, url, timeout=timeout, **kwargs)
    response.raise_for_status()
    return response


def is_backend_alive() -> bool:
    """Check if backend API is reachable.
    
    Returns:
        True if backend is alive, False otherwise
    """
    try:
        response = requests.get(FrontendConfig.API_BASE_URL, timeout=2)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


@st.cache_data(ttl=UIConstants.CACHE_TTL_SHORT)
def fetch_portfolio_daily() -> pd.DataFrame:
    """Fetch daily portfolio data from API.
    
    Returns:
        DataFrame with daily portfolio data
        
    Raises:
        requests.RequestException: On API errors
    """
    response = _make_api_request("GET", APIEndpoints.PORTFOLIO_DAILY)
    return pd.DataFrame(response.json())


@st.cache_data(ttl=UIConstants.CACHE_TTL_SHORT)
def fetch_portfolio_monthly() -> pd.DataFrame:
    """Fetch monthly portfolio data from API.
    
    Returns:
        DataFrame with monthly portfolio data
        
    Raises:
        requests.RequestException: On API errors
    """
    response = _make_api_request("GET", APIEndpoints.PORTFOLIO_MONTHLY)
    return pd.DataFrame(response.json())


@st.cache_data(ttl=UIConstants.CACHE_TTL_MEDIUM)
def fetch_transactions() -> pd.DataFrame:
    """Fetch all transactions from API.
    
    Returns:
        DataFrame with transaction data
        
    Raises:
        requests.RequestException: On API errors
    """
    response = _make_api_request("GET", APIEndpoints.TRANSACTIONS_ALL)
    return pd.DataFrame(response.json())


@st.cache_data(ttl=UIConstants.CACHE_TTL_LONG)
def fetch_isin_mapping() -> Dict[str, Any]:
    """Fetch ISIN to ticker mapping from API.
    
    Returns:
        Dictionary with ISIN mapping
        
    Raises:
        requests.RequestException: On API errors
    """
    response = _make_api_request("GET", APIEndpoints.PORTFOLIO_ISIN_MAPPING)
    return response.json()


def portfolio_data_exists() -> bool:
    """Check if portfolio data is available via API.
    
    Returns:
        True if portfolio data exists, False otherwise
    """
    try:
        response = requests.get(
            FrontendConfig.get_api_url(APIEndpoints.PORTFOLIO_DAILY),
            timeout=5
        )
        return response.status_code == 200
    except:
        return False


def trigger_portfolio_calculation() -> Dict[str, Any]:
    """Trigger portfolio calculation via API.
    
    Returns:
        Response JSON with calculation results
        
    Raises:
        requests.RequestException: On API errors
    """
    response = _make_api_request("POST", APIEndpoints.PORTFOLIO_CALCULATE)
    return response.json()


def trigger_portfolio_refresh() -> Dict[str, Any]:
    """Trigger background portfolio refresh via API.
    
    Returns:
        Response JSON with refresh status
        
    Raises:
        requests.RequestException: On API errors
    """
    response = _make_api_request("POST", APIEndpoints.PORTFOLIO_REFRESH)
    return response.json()


def upload_transactions_file(uploaded_file) -> Optional[Dict[str, Any]]:
    """Upload CSV file to backend via API with validation.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        
    Returns:
        Response JSON with upload results, or None on error
    """
    # Validate file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > UIConstants.MAX_FILE_SIZE_MB:
        st.error(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({UIConstants.MAX_FILE_SIZE_MB}MB)")
        return None
    
    # Validate file type
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in UIConstants.ALLOWED_FILE_TYPES:
        st.error(f"File type '.{file_extension}' not allowed. Allowed types: {', '.join(UIConstants.ALLOWED_FILE_TYPES)}")
        return None
    
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
        response = _make_api_request(
            "POST",
            APIEndpoints.TRANSACTIONS_UPLOAD,
            files=files
        )
        return response.json()
    except requests.RequestException as e:
        st.error(f"Failed to upload file: {e}")
        return None


def cleanup_files(
    input_files: bool = True,
    output_files: bool = True,
    log_files: bool = True
) -> Dict[str, Any]:
    """Clean up application files via API.
    
    Args:
        input_files: Delete files in input directory
        output_files: Delete files in output directory
        log_files: Delete files in logs directory
        
    Returns:
        Response JSON with cleanup results
        
    Raises:
        requests.RequestException: On API errors
    """
    params = {
        "input_files": input_files,
        "output_files": output_files,
        "log_files": log_files
    }
    response = _make_api_request("DELETE", "/core/debug/cleanup", params=params)
    return response.json()


def delete_all_data() -> None:
    """Delete all portfolio data via API.
    
    Raises:
        requests.RequestException: On API errors
    """
    _make_api_request("DELETE", APIEndpoints.DEBUG_DELETE_ALL)
