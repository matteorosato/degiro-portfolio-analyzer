"""Application configuration and settings."""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


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
    
    # Directories
    OUTPUT_DIR: str = "output"
    LOGS_DIR: str = "logs"
    UPLOADS_DIR: str = "uploads"
    
    # File paths
    TRANSACTION_CSV: str = "uploads/Transactions.csv"
    ISIN_MAPPING: str = "output/isin_mapping.json"
    PORTFOLIO_DAILY: str = "output/portfolio_performance_daily.parquet"
    PORTFOLIO_MONTHLY: str = "output/portfolio_performance_monthly.parquet"
    STOCK_PRICES: str = "output/stock_prices.parquet"
    APP_LOG: str = "logs/app.log"
    SCHEDULER_LOG: str = "logs/scheduler.log"


config = AppConfig()


def ensure_directories():
    """Create required directories if they don't exist."""
    for dir_path in [config.OUTPUT_DIR, config.LOGS_DIR, config.UPLOADS_DIR]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
