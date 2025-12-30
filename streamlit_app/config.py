"""Frontend configuration for Streamlit application."""
import os


class FrontendConfig:
    """Configuration for Streamlit frontend."""
    
    # API Configuration
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_V1_PREFIX = "/api/v1"
    API_TIMEOUT = 60  # seconds
    
    # UI Configuration
    PAGE_TITLE = "DeGiro Portfolio Analyzer"
    PAGE_ICON = "📊"
    LAYOUT = "centered"
    
    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Build full API URL from endpoint."""
        return f"{cls.API_BASE_URL}{cls.API_V1_PREFIX}{endpoint}"


class APIEndpoints:
    """API endpoint paths."""
    
    # Transactions
    TRANSACTIONS_UPLOAD = "/transactions/upload"
    TRANSACTIONS_ALL = "/transactions/"
    TRANSACTIONS_PROCESS = "/transactions/process"
    
    # Portfolio
    PORTFOLIO_CALCULATE = "/portfolio/calculate"
    PORTFOLIO_REFRESH = "/portfolio/refresh"
    PORTFOLIO_DAILY = "/portfolio/daily"
    PORTFOLIO_MONTHLY = "/portfolio/monthly"
    PORTFOLIO_ISIN_MAPPING = "/portfolio/isin-mapping"
    
    # Debug
    DEBUG_DELETE_ALL = "/debug/delete-all"


class ColumnMappings:
    """Column name mappings for display."""
    PORTFOLIO_RENAME = {
        'product': 'Product',
        'ticker': 'Ticker',
        'quantity': 'Quantity',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'avg_cost': 'Average Cost (€)',
        'total_cost': 'Total Cost (€)',
        'transaction_costs': 'Transaction Costs (€)',
        'current_value': 'Current Value (€)',
        'current_money_weighted_return': 'Current Money Weighted Return (€)',
        'realized_return': 'Realized Return (€)',
        'net_return': 'Net Return (€)',
        'current_performance_percentage': 'Current Performance (%)',
        'net_performance_percentage': 'Net Performance (%)'
    }

    @staticmethod
    def get_portfolio_columns():
        """Get a copy of the portfolio rename mapping."""
        return ColumnMappings.PORTFOLIO_RENAME.copy()

    @staticmethod
    def get_reverse_mapping(mapping: dict = None):
        """Get reverse mapping from display to original."""
        if mapping is None:
            mapping = ColumnMappings.PORTFOLIO_RENAME
        return {v: k for k, v in mapping.items()}
