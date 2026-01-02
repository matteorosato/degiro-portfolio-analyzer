"""FastAPI routes for transactions domain."""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Optional
from datetime import date
import shutil

from backend.app.shared.logger import app_logger
from backend.app.core.exceptions import TransactionNotFoundError
from backend.app.config import FilePaths, Directories
from .schemas import TransactionResponse, TransactionFilter, TransactionStats
from .services import transaction_service

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "/upload",
    summary="Upload Transactions CSV",
    description="Upload a DeGiro transactions CSV file for processing"
)
async def upload_transactions_csv(file: UploadFile = File(...)):
    """
    Upload and save transactions CSV file.
    
    The file will be saved to the configured input directory and will
    replace any existing transactions file.
    
    Args:
        file: The CSV file to upload (multipart/form-data)
    
    Returns:
        Success message with file info
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only CSV files are allowed."
            )
        
        # Ensure input directory exists
        Directories.ensure_exists(Directories.INPUT)
        
        # Save the uploaded file
        file_path = FilePaths.TRANSACTION_CSV
        with open(file_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        app_logger.info(f"[TRANSACTIONS-API] CSV file uploaded successfully: {file.filename}")
        
        # Process the uploaded file
        df = transaction_service.get_all_transactions()
        
        app_logger.info(f"[TRANSACTIONS-API] Processing {len(df)} transactions...")
        
        # Calculate portfolio with the new transactions
        try:
            from backend.app.routers.portfolio.services import portfolio_service
            portfolio_service.calc_portfolio()
            app_logger.info("[TRANSACTIONS-API] Transactions processed successfully")
            calculation_status = "success"
        except Exception as calc_error:
            app_logger.error(f"[TRANSACTIONS-API] Error when processing transactions: {calc_error}", exc_info=True)
            calculation_status = "failed"
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' uploaded and processed successfully",
            "file_path": file_path,
            "processed_transactions": len(df),
            "portfolio_calculation": calculation_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"[TRANSACTIONS-API] Error uploading file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[TransactionResponse],
    summary="Get All Transactions",
    description="Retrieve all processed transactions from the CSV file"
)
async def get_all_transactions():
    """
    Get all transactions.
    
    Returns a list of all transactions loaded from the DeGiro export file.
    """
    try:
        df = transaction_service.get_all_transactions()
        
        if df.empty:
            app_logger.info("[TRANSACTIONS-API] No transactions found")
            return []
        
        # Convert DataFrame to dict records
        df['Date'] = df['Date'].astype(str)
        if 'Time' in df.columns:
            df['Time'] = df['Time'].astype(str)
        
        transactions = df.to_dict(orient="records")
        app_logger.info(f"[TRANSACTIONS-API] Returning {len(transactions)} transactions")
        
        return transactions
        
    except Exception as e:
        app_logger.error(f"[TRANSACTIONS-API] Error fetching transactions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transactions: {str(e)}"
        )


@router.get(
    "/filter",
    response_model=List[TransactionResponse],
    summary="Get Filtered Transactions",
    description="Retrieve transactions with optional filters"
)
async def get_filtered_transactions(
    isin: Optional[str] = Query(None, description="Filter by ISIN code"),
    stock: Optional[str] = Query(None, description="Filter by stock ticker"),
    action: Optional[str] = Query(None, description="Filter by action (BUY/SELL)"),
    start_date: Optional[date] = Query(None, description="Filter from date"),
    end_date: Optional[date] = Query(None, description="Filter to date")
):
    """
    Get transactions with filters.
    
    Apply various filters to narrow down the transaction list.
    """
    try:
        # Convert dates to string for service layer
        start_str = start_date.isoformat() if start_date else None
        end_str = end_date.isoformat() if end_date else None
        
        df = transaction_service.get_filtered_transactions(
            isin=isin,
            stock=stock,
            action=action,
            start_date=start_str,
            end_date=end_str
        )
        
        if df.empty:
            return []
        
        # Convert to response format
        df['Date'] = df['Date'].astype(str)
        if 'Time' in df.columns:
            df['Time'] = df['Time'].astype(str)
        
        return df.to_dict(orient="records")
        
    except Exception as e:
        app_logger.error(f"[TRANSACTIONS-API] Error filtering: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    response_model=TransactionStats,
    summary="Get Transaction Statistics",
    description="Get overview statistics about all transactions"
)
async def get_transaction_statistics():
    """
    Get transaction statistics.
    
    Returns aggregated statistics like total transactions, buys/sells,
    unique stocks, date range, and totals.
    """
    try:
        stats = transaction_service.get_transaction_stats()
        return stats
        
    except Exception as e:
        app_logger.error(f"[TRANSACTIONS-API] Error calculating stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{isin}",
    response_model=List[TransactionResponse],
    summary="Get Transactions by ISIN",
    description="Retrieve all transactions for a specific ISIN"
)
async def get_transactions_by_isin(isin: str):
    """
    Get all transactions for a specific ISIN.
    
    Args:
        isin: International Securities Identification Number
    """
    try:
        df = transaction_service.get_filtered_transactions(isin=isin)
        
        if df.empty:
            raise TransactionNotFoundError()
        
        df['Date'] = df['Date'].astype(str)
        if 'Time' in df.columns:
            df['Time'] = df['Time'].astype(str)
        
        return df.to_dict(orient="records")
        
    except TransactionNotFoundError:
        raise
    except Exception as e:
        app_logger.error(f"[TRANSACTIONS-API] Error fetching {isin}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
