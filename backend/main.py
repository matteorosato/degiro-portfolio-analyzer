import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.api.routes import portfolio, transactions, db_refresh, logs, debug
from backend.utils.scheduler import start_scheduled_tasks
from backend.utils.logger import app_logger


# Load .env only in development mode
DEV_MODE = os.getenv("DEV_MODE", "False").lower() in ("true", "1", "yes")
if DEV_MODE:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=".env")  # Safe even if the file is missing
    app_logger.info("[STARTUP] .env file loaded in DEV_MODE (api)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduled_tasks()
    app_logger.info("[STARTUP] Scheduled tasks initialized.")
    yield
    # Shutdown
    app_logger.info("[SHUTDOWN] App is shutting down.")


app = FastAPI(
    title="Portfolio Analyzer API",
    description="API to manage and calculate portfolio data.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routes
app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(db_refresh.router, prefix="/db", tags=["Database"])
app.include_router(logs.router, prefix="/logs", tags=["Logs"])
app.include_router(debug.router, prefix="/debug", tags=["Debug"])


@app.get("/", tags=["Root"])
async def read_root():
    """Health check endpoint to confirm the API is running."""
    return {"message": "Portfolio Analyzer API is running"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
