"""Pydantic schemas for transactions domain."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, time


class TransactionResponse(BaseModel):
    """Response model for a single transaction."""
    
    Date: Optional[date] = None
    Time: Optional[time] = None
    Product_Name_DeGiro: Optional[str] = Field(None, description="Product name from DeGiro")
    ISIN: str = Field(..., description="International Securities Identification Number")
    Exchange: Optional[str] = Field(None, description="Stock exchange")
    Quantity: float = Field(..., description="Number of shares")
    Price: float = Field(..., description="Price per share")
    Currency: str = Field(..., description="Currency code (e.g., EUR, USD)")
    Cost: float = Field(..., description="Total cost of transaction")
    Transaction_costs: float = Field(..., alias="Transaction_costs", description="Broker fees")
    Stock: str = Field(..., description="Stock ticker symbol")
    Product: str = Field(..., description="Product type (Stock, ETF, etc.)")
    Action: str = Field(..., description="BUY or SELL")
    
    model_config = {"populate_by_name": True}


class TransactionFilter(BaseModel):
    """Filter parameters for transactions query."""
    
    isin: Optional[str] = Field(None, description="Filter by ISIN")
    stock: Optional[str] = Field(None, description="Filter by stock ticker")
    action: Optional[str] = Field(None, description="Filter by action (BUY/SELL)")
    start_date: Optional[date] = Field(None, description="Filter from this date")
    end_date: Optional[date] = Field(None, description="Filter until this date")
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action field."""
        if v and v not in ['BUY', 'SELL', 'DIVIDEND']:
            raise ValueError('Action must be BUY, SELL, or DIVIDEND')
        return v


class TransactionStats(BaseModel):
    """Statistics about transactions."""
    
    total_transactions: int
    total_buys: int
    total_sells: int
    unique_stocks: int
    date_range: dict
    total_invested: float
    total_fees: float
