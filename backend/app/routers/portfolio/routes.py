"""Portfolio domain routes."""
from fastapi import APIRouter, BackgroundTasks
from backend.app.routers.portfolio.schemas import (
    CalculationResponse,
    RefreshStatusResponse
)
from backend.app.routers.portfolio.services import portfolio_service
from backend.app.routers.portfolio.tasks import background_refresh_task
from backend.app.shared.logger import app_logger
from backend.app.shared.refresh_status import get_refresh_status, is_refresh_running
from backend.app.core.exceptions import RefreshInProgressError, PortfolioCalculationError

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/calculate", response_model=CalculationResponse)
async def calculate_portfolio():
    """Trigger synchronous portfolio calculation.
    
    This endpoint calculates the portfolio performance immediately and blocks until complete.
    Use the /refresh endpoint for background processing.
    
    Returns:
        CalculationResponse: Success message with status
        
    Raises:
        PortfolioCalculationError: If calculation fails
    """
    try:
        app_logger.info("[API] Portfolio calculation requested")
        portfolio_service.calc_portfolio()
        app_logger.info("[API] Portfolio calculation completed successfully")
        
        return CalculationResponse(
            message="Portfolio calculation completed successfully",
            success=True
        )
    except Exception as e:
        app_logger.error(f"[API] Portfolio calculation failed: {e}", exc_info=True)
        raise PortfolioCalculationError(f"Portfolio calculation failed: {str(e)}")


@router.post("/refresh", response_model=CalculationResponse)
async def refresh_portfolio(background_tasks: BackgroundTasks):
    """Trigger background portfolio refresh.
    
    This endpoint starts a background task to recalculate the portfolio and returns immediately.
    Use the /refresh/status endpoint to check progress.
    
    Args:
        background_tasks: FastAPI background tasks handler
        
    Returns:
        CalculationResponse: Message indicating refresh has started
        
    Raises:
        RefreshInProgressError: If a refresh is already running
    """
    if is_refresh_running():
        app_logger.warning("[API] Portfolio refresh requested but already in progress")
        raise RefreshInProgressError("Portfolio refresh already in progress")
    
    app_logger.info("[API] Portfolio background refresh requested")
    background_tasks.add_task(background_refresh_task)
    
    return CalculationResponse(
        message="Portfolio refresh started in background",
        success=True
    )


@router.get("/refresh/status", response_model=RefreshStatusResponse)
async def get_refresh_status_route():
    """Get current portfolio refresh status.
    
    Returns the current state of the background refresh task including:
    - Status (idle, running, completed, failed)
    - Start and completion timestamps
    - Error message if failed
    
    Returns:
        RefreshStatusResponse: Current refresh status with timestamps
    """
    app_logger.info("[API] Refresh status requested")
    state = get_refresh_status()
    
    return RefreshStatusResponse(
        status=state.status,
        started_at=state.started_at.isoformat() if state.started_at else None,
        completed_at=state.completed_at.isoformat() if state.completed_at else None,
        error_message=state.error_message
    )
