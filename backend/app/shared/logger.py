"""Logging configuration for the application."""
import logging
from logging.handlers import RotatingFileHandler
import os

from backend.app.core.config import config

# Ensure logs directory exists
os.makedirs(config.LOGS_DIR, exist_ok=True)

# ---- App Logger ----
app_logger = logging.getLogger("portfolio-analyzer")
app_logger.setLevel(logging.INFO)

app_log_file = config.APP_LOG
app_handler = RotatingFileHandler(app_log_file, maxBytes=5*1024*1024, backupCount=3)
app_formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
app_handler.setFormatter(app_formatter)
app_logger.addHandler(app_handler)

# ---- Scheduler Logger ----
scheduler_logger = logging.getLogger("portfolio-scheduler")
scheduler_logger.setLevel(logging.INFO)

scheduler_log_file = config.SCHEDULER_LOG
scheduler_handler = RotatingFileHandler(scheduler_log_file, maxBytes=5*1024*1024, backupCount=3)
scheduler_handler.setFormatter(app_formatter)
scheduler_logger.addHandler(scheduler_handler)
