"""Background tasks for portfolio domain."""
from backend.app.shared.logger import app_logger
from backend.app.shared.refresh_status import (
    set_refresh_running,
    set_refresh_completed,
    set_refresh_failed
)
from backend.app.routers.portfolio.services import portfolio_service


async def background_refresh_task() -> None:
    """Background task for portfolio refresh.
    
    This task:
    1. Sets refresh status to running
    2. Executes portfolio calculation
    3. Updates refresh status on completion or failure
    
    Used by FastAPI's BackgroundTasks to run asynchronously without blocking the API response.
    """
    try:
        app_logger.info("[PORTFOLIO-REFRESH] Starting background portfolio refresh...")
        set_refresh_running()
        
        # Execute portfolio calculation
        portfolio_service.calc_portfolio()
        
        app_logger.info("[PORTFOLIO-REFRESH] Background portfolio refresh completed successfully.")
        set_refresh_completed()
        
    except Exception as e:
        app_logger.error(
            f"[PORTFOLIO-REFRESH] Error during background portfolio refresh: {e}", 
            exc_info=True
        )
        set_refresh_failed(str(e))
        raise
