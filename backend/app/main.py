"""Main FastAPI application entry point."""
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings, config, ensure_directories
from backend.app.shared.logger import app_logger
from backend.app.shared.scheduler import start_scheduled_tasks
from backend.app.routers.transactions import router as transactions_router
from backend.app.routers.portfolio import router as portfolio_router
from backend.app.routers.core import router as core_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events.
    
    Startup:
    - Ensures required directories exist
    - Starts scheduled background tasks
    
    Shutdown:
    - Logs shutdown event
    """
    # Startup
    app_logger.info("[STARTUP] Starting Portfolio Analyzer API...")
    
    # Ensure directories exist
    ensure_directories()
    app_logger.info("[STARTUP] Directories verified.")
    
    # Start scheduled tasks
    start_scheduled_tasks()
    app_logger.info("[STARTUP] Scheduled tasks initialized.")
    
    yield
    
    # Shutdown
    app_logger.info("[SHUTDOWN] Portfolio Analyzer API is shutting down.")


# Create FastAPI application
app = FastAPI(
    title=config.PROJECT_NAME,
    description=config.DESCRIPTION,
    version=config.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with API versioning
API_V1_PREFIX = "/api/v1"
app.include_router(transactions_router, prefix=API_V1_PREFIX)
app.include_router(portfolio_router, prefix=API_V1_PREFIX)
app.include_router(core_router, prefix=API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API health check.
    
    Returns basic information about the API.
    Use /api/v1/core/health for detailed health check.
    """
    return {
        "message": f"{config.PROJECT_NAME} is running",
        "version": config.API_VERSION,
        "docs": "/docs",
        "health": f"{API_V1_PREFIX}/core/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEV_MODE,
    )
