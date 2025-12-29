"""Custom exceptions for the application."""
from fastapi import HTTPException, status


class PortfolioCalculationError(HTTPException):
    """Raised when portfolio calculation fails."""
    
    def __init__(self, detail: str = "Portfolio calculation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class TransactionNotFoundError(HTTPException):
    """Raised when requested transaction is not found."""
    
    def __init__(self, detail: str = "Transaction not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class RefreshInProgressError(HTTPException):
    """Raised when trying to start refresh while one is already running."""
    
    def __init__(self, detail: str = "Portfolio refresh already in progress"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class InvalidDataError(HTTPException):
    """Raised when input data is invalid."""
    
    def __init__(self, detail: str = "Invalid data provided"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
