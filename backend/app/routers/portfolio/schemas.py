"""Pydantic schemas for portfolio domain."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class PortfolioHoldingResponse(BaseModel):
    """Single portfolio holding response."""
    
    product: str = Field(..., description="Product name")
    ticker: str = Field(..., description="Stock ticker symbol")
    quantity: float = Field(..., description="Number of shares held")
    start_date: date = Field(..., description="First purchase date")
    end_date: Optional[date] = Field(None, description="Last sale date (if sold)")
    avg_cost: float = Field(..., description="Average cost per share")
    total_cost: float = Field(..., description="Total invested")
    transaction_costs: float = Field(..., description="Total fees paid")
    current_value: float = Field(..., description="Current market value")
    current_money_weighted_return: float = Field(..., description="Current unrealized return")
    realized_return: float = Field(..., description="Realized gains/losses")
    net_return: float = Field(..., description="Total return (realized + unrealized)")
    current_performance_percentage: float = Field(..., description="Current performance %")
    net_performance_percentage: float = Field(..., description="Net performance %")


class RefreshStatusResponse(BaseModel):
    """Portfolio refresh status response."""
    
    status: str = Field(..., description="Current status: idle, running, completed, failed")
    started_at: Optional[str] = Field(None, description="When refresh started (ISO format)")
    completed_at: Optional[str] = Field(None, description="When refresh completed (ISO format)")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class CalculationResponse(BaseModel):
    """Portfolio calculation trigger response."""
    
    message: str
    success: bool = True
