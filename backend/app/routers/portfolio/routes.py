"""Portfolio domain routes."""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Body
from typing import Optional, Dict, Any
from fastapi.responses import JSONResponse
import pandas as pd
import json
import os

from backend.app.routers.portfolio.schemas import (
    CalculationResponse,
    RefreshStatusResponse
)
from backend.app.routers.portfolio.services import portfolio_service
from backend.app.routers.portfolio.tasks import background_refresh_task
from backend.app.shared.logger import app_logger
from backend.app.shared.refresh_status import get_refresh_status, is_refresh_running
from backend.app.core.exceptions import RefreshInProgressError, PortfolioCalculationError
from backend.app.config import FilePaths

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


@router.get("/daily")
async def get_portfolio_daily(
    ticker: Optional[str] = Query(None, description="Filter by ticker/product"),
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    limit: int = Query(10000, le=50000, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """Get daily portfolio performance data with optional filtering.
    
    Returns the processed daily portfolio performance data as JSON.
    Supports filtering by ticker, date range, and pagination.
    
    Args:
        ticker: Filter by specific ticker/product name
        start_date: Filter records from this date onwards
        end_date: Filter records up to this date
        limit: Maximum number of records to return (default: 10000, max: 50000)
        offset: Number of records to skip for pagination
    
    Returns:
        JSON array of daily portfolio records
        
    Raises:
        HTTPException: If portfolio data file doesn't exist or can't be read
    """
    try:
        if not os.path.exists(FilePaths.PORTFOLIO_DAILY):
            raise HTTPException(
                status_code=404,
                detail="Portfolio daily data not found. Run calculation first."
            )
        
        df = pd.read_parquet(FilePaths.PORTFOLIO_DAILY)
        
        # Apply filters
        if ticker:
            df = df[df['ticker'] == ticker]
        
        if start_date or end_date:
            df['end_date'] = pd.to_datetime(df['end_date'])
            if start_date:
                df = df[df['end_date'] >= start_date]
            if end_date:
                df = df[df['end_date'] <= end_date]
        
        # Apply pagination
        total_records = len(df)
        df = df.iloc[offset:offset + limit]
        
        # Convert date columns to string for JSON serialization
        date_columns = df.select_dtypes(include=['datetime64']).columns
        for col in date_columns:
            df[col] = df[col].astype(str)
        
        data = df.to_dict(orient="records")
        app_logger.info(f"[API] Returning {len(data)} of {total_records} daily portfolio records (offset={offset}, limit={limit})")
        
        return JSONResponse(content=data)
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"[API] Error reading daily portfolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read portfolio data: {str(e)}"
        )


@router.get("/isin-mapping")
async def get_isin_mapping():
    """Get ISIN to ticker mapping data.
    
    Returns the mapping between ISIN codes and stock tickers,
    including product names and other metadata.
    
    Returns:
        JSON object with ISIN mapping data
        
    Raises:
        HTTPException: If mapping file doesn't exist or can't be read
    """
    try:
        if not os.path.exists(FilePaths.ISIN_MAPPING):
            raise HTTPException(
                status_code=404,
                detail="ISIN mapping not found. Upload and process transactions first."
            )
        
        with open(FilePaths.ISIN_MAPPING, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
        
        app_logger.info(f"[API] Returning ISIN mapping with {len(mapping_data)} entries")
        
        return JSONResponse(content=mapping_data)
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"[API] Error reading ISIN mapping: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read ISIN mapping: {str(e)}"
        )


@router.post("/isin-mapping")
async def save_isin_mapping(mapping_data: Dict[str, Any] = Body(...)):
    """Update ISIN to ticker mapping data.
    
    Replaces the entire ISIN mapping file with new data.
    
    Args:
        mapping_data: Dictionary with ISIN codes as keys and mapping metadata as values
        
    Returns:
        JSON response with success message and number of entries saved
        
    Raises:
        HTTPException: If save operation fails
    """
    try:
        if not mapping_data:
            raise HTTPException(
                status_code=400,
                detail="Mapping data cannot be empty"
            )
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(FilePaths.ISIN_MAPPING), exist_ok=True)
        
        # Save mapping to file
        with open(FilePaths.ISIN_MAPPING, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=4, ensure_ascii=False)
        
        app_logger.info(f"[API] ISIN mapping updated successfully with {len(mapping_data)} entries")
        
        return JSONResponse(
            content={
                "message": "ISIN mapping updated successfully",
                "entries_saved": len(mapping_data),
                "success": True
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"[API] Error updating ISIN mapping: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update ISIN mapping: {str(e)}"
        )
