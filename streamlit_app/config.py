"""Frontend configuration for Streamlit application."""
import os


class FrontendConfig:
    """Configuration for Streamlit frontend."""

    # API Configuration
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_V1_PREFIX = "/api/v1"
    API_TIMEOUT = 60  # seconds

    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Build full API URL from endpoint."""
        return f"{cls.API_BASE_URL}{cls.API_V1_PREFIX}{endpoint}"


class UIConstants:
    """UI constants for consistent styling and layout."""

    # Table/Dataframe
    TABLE_ROW_HEIGHT = 50
    TABLE_BASE_HEIGHT = 37

    # Cache TTL (seconds)
    CACHE_TTL_SHORT = 60  # 1 minute
    CACHE_TTL_MEDIUM = 300  # 5 minutes
    CACHE_TTL_LONG = 3600  # 1 hour

    # File Upload
    MAX_FILE_SIZE_MB = 50
    ALLOWED_FILE_TYPES = ["csv"]

    # Analysis Page
    TREND_DAYS = 30
    HOLDINGS_OPTIONS = ["Current Holdings", "All Holdings"]
    FULL_PORTFOLIO_NAME = "Full portfolio"

    @staticmethod
    def calculate_table_height(row_count: int) -> int:
        """Calculate table height based on row count."""
        return UIConstants.TABLE_ROW_HEIGHT * row_count + UIConstants.TABLE_BASE_HEIGHT


class ColorScheme:
    """Color scheme for consistent UI styling."""

    POSITIVE = "#09ab3b"
    NEGATIVE = "#ff2b2b"
    NEUTRAL = "gray"

    # Product type colors
    PRODUCT_TYPE_COLORS = {
        "ETF": "#1f77b4",
        "Stock": "orange",
        "Other": "purple"
    }


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
