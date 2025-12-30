"""Core infrastructure routes - health checks, debugging, and logs."""
from fastapi import APIRouter, HTTPException
from typing import List
from backend.app.config import settings, config
from backend.app.shared.logger import app_logger
from backend.app.shared.scheduler import scheduled_portfolio_job

router = APIRouter(prefix="/core", tags=["Core"])


@router.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns basic application status and configuration info.
    Useful for monitoring and deployment health checks.
    
    Returns:
        dict: Application status information
    """
    return {
        "status": "healthy",
        "app": config.PROJECT_NAME,
        "version": config.API_VERSION,
        "environment": "development" if settings.DEV_MODE else "production"
    }


@router.get("/debug/trigger/calculate")
async def trigger_portfolio_calculation():
    """Manually trigger portfolio calculation job.
    
    This endpoint bypasses the scheduler and runs the portfolio calculation immediately.
    Useful for debugging and manual testing.
    
    Returns:
        dict: Success message
    """
    app_logger.info("[DEBUG] Manual portfolio calculation triggered")
    scheduled_portfolio_job()
    return {"message": "Portfolio calculation job triggered manually"}


@router.get("/logs/scheduler", response_model=List[str])
async def read_scheduler_logs(lines: int = 50):
    """Read last N lines from scheduler log file.
    
    Args:
        lines: Number of lines to return from end of file (default: 50)
        
    Returns:
        List of log lines
        
    Raises:
        HTTPException: If log file not found
    """
    try:
        with open(config.SCHEDULER_LOG, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Scheduler log file not found")


@router.get("/logs/app", response_model=List[str])
async def read_app_logs(lines: int = 50):
    """Read last N lines from application log file.
    
    Args:
        lines: Number of lines to return from end of file (default: 50)
        
    Returns:
        List of log lines
        
    Raises:
        HTTPException: If log file not found
    """
    try:
        with open(config.APP_LOG, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Application log file not found")
