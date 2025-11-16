import os
import pandas as pd
from backend.utils.logger import app_logger
from backend.config import FilePaths

# All Supabase and DB logic has been removed. Only local Parquet file refresh logic remains or is skipped.

def db_refresh():
    app_logger.info("[DB-REFRESH] Supabase support has been removed. No database refresh will be performed.")
    return
