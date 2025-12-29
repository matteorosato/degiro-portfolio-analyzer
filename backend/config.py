import os
from pathlib import Path


# Environment Variables
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"


class Environment:
    """Environment configuration."""
    API_HOST = os.getenv("API_HOST", "localhost")
    API_PORT = int(os.getenv("API_PORT", "8000"))


class Directories:
    """Directory paths."""
    OUTPUT = "output"
    LOGS = "logs"
    UPLOADS = "uploads"

    @staticmethod
    def ensure_exists(directory: str):
        """Ensure a directory exists."""
        Path(directory).mkdir(parents=True, exist_ok=True)


class FilePaths:
    """File paths."""
    PORTFOLIO_DAILY = os.path.join(Directories.OUTPUT, "portfolio_performance_daily.parquet")
    PORTFOLIO_MONTHLY = os.path.join(Directories.OUTPUT, "portfolio_performance_monthly.parquet")
    STOCK_PRICES = os.path.join(Directories.OUTPUT, "stock_prices.parquet")
    ISIN_MAPPING = os.path.join(Directories.OUTPUT, "isin_mapping.json")
    TRANSACTION_CSV = os.path.join(Directories.UPLOADS, "Transactions.csv")
    APP_LOG = os.path.join(Directories.LOGS, "app.log")
    SCHEDULER_LOG = os.path.join(Directories.LOGS, "scheduler.log")

    @staticmethod
    def get_all_output_files():
        """Get list of all output files."""
        return [
            FilePaths.PORTFOLIO_DAILY,
            FilePaths.PORTFOLIO_MONTHLY,
            FilePaths.STOCK_PRICES,
            FilePaths.ISIN_MAPPING,
        ]


class APIEndpoints:
    """API endpoint paths (with /api/v1 prefix)."""
    PORTFOLIO_CALCULATE = f"{API_V1_PREFIX}/portfolio/calculate"
    PORTFOLIO_REFRESH = f"{API_V1_PREFIX}/portfolio/refresh"
    TRANSACTIONS_ALL = f"{API_V1_PREFIX}/transactions/"

    @staticmethod
    def build_url(endpoint: str, base_url: str = None) -> str:
        """Build full URL from base and endpoint."""
        base = base_url or API_BASE_URL
        return f"{base}{endpoint}"


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