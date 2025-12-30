"""Custom validators for transactions domain."""
import re


def validate_isin(isin: str) -> bool:
    """
    Validate ISIN format.
    
    ISIN format: 2 letter country code + 9 alphanumeric + 1 check digit
    Example: US0378331005 (Apple Inc.)
    
    Args:
        isin: ISIN string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isin or len(isin) != 12:
        return False
    
    # Check format: 2 letters + 10 alphanumeric
    pattern = r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$'
    return bool(re.match(pattern, isin))


def validate_ticker(ticker: str) -> bool:
    """
    Validate stock ticker format.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        True if valid, False otherwise
    """
    if not ticker or len(ticker) > 10:
        return False
    # Tickers are usually uppercase letters, sometimes with dots
    pattern = r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$'
    return bool(re.match(pattern, ticker))


def validate_currency(currency: str) -> bool:
    """
    Validate currency code (ISO 4217).
    
    Args:
        currency: Currency code
        
    Returns:
        True if valid, False otherwise
    """
    valid_currencies = ['EUR', 'USD', 'GBP', 'CHF', 'JPY', 'CAD', 'AUD']
    return currency in valid_currencies


def validate_transaction_data(transaction: dict) -> tuple[bool, str]:
    """
    Validate transaction data integrity.
    
    Args:
        transaction: Transaction dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    required_fields = ['ISIN', 'Quantity', 'Price', 'Price_Currency', 'Action']
    for field in required_fields:
        if field not in transaction or transaction[field] is None:
            return False, f"Missing required field: {field}"
    
    # Validate ISIN
    if not validate_isin(transaction['ISIN']):
        return False, f"Invalid ISIN format: {transaction['ISIN']}"
    
    # Validate quantities
    if transaction['Quantity'] <= 0:
        return False, "Quantity must be positive"
    
    if transaction['Price'] <= 0:
        return False, "Price must be positive"
    
    # Validate currency
    if not validate_currency(transaction['Price_Currency']):
        return False, f"Invalid currency: {transaction['Price_Currency']}"
    
    return True, ""
