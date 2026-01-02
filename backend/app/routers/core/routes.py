"""Core infrastructure routes - health checks, debugging, and logs."""
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

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


@router.delete("/debug/cleanup")
async def cleanup_files(
        input_files: bool = True,
        output_files: bool = True,
        log_files: bool = True
):
    """Clean up application files and directories.
    
    This endpoint allows selective deletion of files in input, output, and logs directories.
    Useful for resetting the application state during development or troubleshooting.
    
    Args:
        input_files: Delete files in input directory (default: True)
        output_files: Delete files in output directory (default: True)
        log_files: Delete files in logs directory (default: True)
        
    Returns:
        dict: Summary of deleted files and directories
        
    Note:
        Directories are preserved, only their contents are deleted.
    """
    deleted_items = {
        "input_files": [],
        "output_files": [],
        "log_files": []
    }

    try:
        # Clean input directory
        if input_files:
            input_dir = Path(config.INPUT_DIR)
            if input_dir.exists():
                for item in input_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                        deleted_items["input_files"].append(item.name)
                        app_logger.info(f"Deleted input file: {item.name}")

        # Clean output directory
        if output_files:
            output_dir = Path(config.OUTPUT_DIR)
            if output_dir.exists():
                for item in output_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                        deleted_items["output_files"].append(item.name)
                        app_logger.info(f"Deleted output file: {item.name}")

        total_deleted = sum(len(files) for files in deleted_items.values())

        return {
            "status": "success",
            "message": f"Cleanup completed. Deleted {total_deleted} file(s).",
            "deleted": deleted_items
        }

    except Exception as e:
        app_logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
