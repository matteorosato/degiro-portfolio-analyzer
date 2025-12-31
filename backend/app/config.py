"""Centralized application configuration."""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


# Environment Variables
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1"

# Project root directory (config.py is 3 levels deep: backend/app/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()


class Settings(BaseSettings):
    """Environment-specific settings loaded from .env file."""
    
    # Environment
    DEV_MODE: bool = False
    
    # API Server
    API_HOST: str = "localhost"
    API_PORT: int = 8000
    
    # CORS Settings
    cors_origins_raw: str = "*"
    
    model_config = {"env_file": ".env", "case_sensitive": True}
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS origins from comma-separated string to list."""
        if isinstance(self.cors_origins_raw, list):
            return self.cors_origins_raw
        return [origin.strip() for origin in self.cors_origins_raw.split(",")]


settings = Settings()


class AppConfig:
    """Application-wide constants (not environment-specific)."""
    
    # API Info
    PROJECT_NAME: str = "Portfolio Analyzer API"
    VERSION: str = "1.0.0"
    API_VERSION: str = "1.0.0"  # Alias for VERSION
    API_V1_PREFIX: str = "/api/v1"
    DESCRIPTION: str = "API to manage and calculate portfolio data"
    
    # Directories (absolute paths)
    INPUT_DIR: str = str(PROJECT_ROOT / "backend" / "input")
    OUTPUT_DIR: str = str(PROJECT_ROOT / "backend" / "output")
    LOGS_DIR: str = str(PROJECT_ROOT / "backend" / "logs")
    CACHE_DIR: str = str(PROJECT_ROOT / "backend" / "cache")
    
    # File paths (absolute paths)
    TRANSACTION_CSV: str = str(PROJECT_ROOT / "backend" / "input" / "transactions.csv")
    ISIN_MAPPING: str = str(PROJECT_ROOT / "backend" / "output" / "isin_mapping.json")
    PORTFOLIO_DAILY: str = str(PROJECT_ROOT / "backend" / "output" / "portfolio_performance_daily.parquet")
    STOCK_PRICES: str = str(PROJECT_ROOT / "backend" / "output" / "stock_prices.parquet")
    APP_LOG: str = str(PROJECT_ROOT / "backend" / "logs" / "app.log")
    SCHEDULER_LOG: str = str(PROJECT_ROOT / "backend" / "logs" / "scheduler.log")


class Environment:
    """Environment configuration."""
    API_HOST = os.getenv("API_HOST", "localhost")
    API_PORT = int(os.getenv("API_PORT", "8000"))


class Directories:
    """Directory paths."""
    INPUT = AppConfig.INPUT_DIR
    OUTPUT = AppConfig.OUTPUT_DIR
    LOGS = AppConfig.LOGS_DIR

    @staticmethod
    def ensure_exists(directory: str):
        """Ensure a directory exists."""
        Path(directory).mkdir(parents=True, exist_ok=True)


class FilePaths:
    """File paths."""
    PORTFOLIO_DAILY = AppConfig.PORTFOLIO_DAILY
    STOCK_PRICES = AppConfig.STOCK_PRICES
    ISIN_MAPPING = AppConfig.ISIN_MAPPING
    TRANSACTION_CSV = AppConfig.TRANSACTION_CSV
    APP_LOG = AppConfig.APP_LOG
    SCHEDULER_LOG = AppConfig.SCHEDULER_LOG

    @staticmethod
    def get_all_output_files():
        """Get list of all output files."""
        return [
            FilePaths.PORTFOLIO_DAILY,
            FilePaths.STOCK_PRICES,
            FilePaths.ISIN_MAPPING,
        ]


config = AppConfig()


def ensure_directories():
    """Create required directories if they don't exist."""
    for dir_path in [config.INPUT_DIR, config.OUTPUT_DIR, config.LOGS_DIR, config.CACHE_DIR]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
