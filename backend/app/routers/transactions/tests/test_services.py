"""Unit tests for transaction services."""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from backend.app.routers.transactions.services import TransactionService, transaction_service
from backend.app.routers.transactions.validators import (
    validate_isin,
    validate_ticker,
    validate_currency,
    validate_transaction_data
)


class TestTransactionService:
    """Test TransactionService class."""
    
    @pytest.fixture
    def service(self):
        """Create a TransactionService instance."""
        return TransactionService()
    
    @pytest.fixture
    def sample_transactions_df(self):
        """Create sample transaction DataFrame."""
        return pd.DataFrame({
            'Date': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'Time': ['10:00:00', '11:00:00'],
            'ISIN': ['US0378331005', 'US5949181045'],
            'Stock': ['AAPL', 'MSFT'],
            'Action': ['BUY', 'SELL'],
            'Quantity': [10.0, 5.0],
            'Price': [150.0, 380.0],
            'Currency': ['USD', 'USD'],
            'Cost': [1500.0, 1900.0],
            'Transaction_costs': [1.0, 1.5],
            'Product': ['Apple Inc.', 'Microsoft Corp.'],
            'Product_Name_DeGiro': ['Apple', 'Microsoft'],
            'Exchange': ['NDQ', 'NDQ']
        })
    
    def test_prepare_data_empty(self, service):
        """Test prepare data with empty DataFrame."""
        df = service._prepare_data(pd.DataFrame())
        assert df.empty
    
    @patch('backend.app.routers.transactions.services.pd.read_csv')
    def test_load_data_success(self, mock_read_csv, service):
        """Test successful data loading."""
        # Create mock CSV data
        mock_df = pd.DataFrame([[
            '01-01-2024', '10:00', 'AAPL', 'US0378331005', 'NDQ', '',
            '10', '150', 'USD', '1500', 'USD', '1500', 'USD', '1',
            '1', 'USD', '1501', 'USD', '12345'
        ]])
        mock_read_csv.return_value = mock_df
        
        with patch.object(Path, 'exists', return_value=True):
            df = service._load_data()
        
        assert not df.empty
        assert 'Date' in df.columns
        assert 'ISIN' in df.columns
    
    def test_get_transaction_stats_empty(self, service):
        """Test stats with empty DataFrame."""
        with patch.object(service, 'get_all_transactions', return_value=pd.DataFrame()):
            stats = service.get_transaction_stats()
        
        assert stats['total_transactions'] == 0
        assert stats['total_buys'] == 0
        assert stats['total_sells'] == 0
    
    def test_get_transaction_stats(self, service, sample_transactions_df):
        """Test stats calculation."""
        with patch.object(service, 'get_all_transactions', return_value=sample_transactions_df):
            stats = service.get_transaction_stats()
        
        assert stats['total_transactions'] == 2
        assert stats['total_buys'] == 1
        assert stats['total_sells'] == 1
        assert stats['unique_stocks'] == 2
    
    def test_get_filtered_transactions(self, service, sample_transactions_df):
        """Test filtering transactions."""
        with patch.object(service, 'get_all_transactions', return_value=sample_transactions_df):
            filtered = service.get_filtered_transactions(action='BUY')
        
        assert len(filtered) == 1
        assert filtered['Action'].iloc[0] == 'BUY'


class TestValidators:
    """Test validation functions."""
    
    def test_validate_isin_valid(self):
        """Test valid ISIN codes."""
        assert validate_isin('US0378331005') is True  # Apple
        assert validate_isin('IE00B4L5Y983') is True  # iShares ETF
        assert validate_isin('NL0000009165') is True  # Airbus
    
    def test_validate_isin_invalid(self):
        """Test invalid ISIN codes."""
        assert validate_isin('INVALID') is False
        assert validate_isin('US037833100') is False  # Too short
        assert validate_isin('') is False
        assert validate_isin('us0378331005') is False  # Lowercase
    
    def test_validate_ticker_valid(self):
        """Test valid ticker symbols."""
        assert validate_ticker('AAPL') is True
        assert validate_ticker('BRK.B') is True
        assert validate_ticker('MSFT') is True
    
    def test_validate_ticker_invalid(self):
        """Test invalid ticker symbols."""
        assert validate_ticker('toolongname') is False
        assert validate_ticker('123') is False
        assert validate_ticker('') is False
    
    def test_validate_currency_valid(self):
        """Test valid currency codes."""
        assert validate_currency('EUR') is True
        assert validate_currency('USD') is True
        assert validate_currency('GBP') is True
    
    def test_validate_currency_invalid(self):
        """Test invalid currency codes."""
        assert validate_currency('XXX') is False
        assert validate_currency('eur') is False
        assert validate_currency('') is False
    
    def test_validate_transaction_data_valid(self):
        """Test valid transaction data."""
        transaction = {
            'ISIN': 'US0378331005',
            'Quantity': 10.0,
            'Price': 150.0,
            'Currency': 'USD',
            'Action': 'BUY'
        }
        is_valid, error = validate_transaction_data(transaction)
        assert is_valid is True
        assert error == ""
    
    def test_validate_transaction_data_missing_field(self):
        """Test transaction with missing required field."""
        transaction = {
            'ISIN': 'US0378331005',
            'Quantity': 10.0,
            # Missing Price
            'Currency': 'USD',
            'Action': 'BUY'
        }
        is_valid, error = validate_transaction_data(transaction)
        assert is_valid is False
        assert "Missing required field: Price" in error
    
    def test_validate_transaction_data_invalid_isin(self):
        """Test transaction with invalid ISIN."""
        transaction = {
            'ISIN': 'INVALID',
            'Quantity': 10.0,
            'Price': 150.0,
            'Currency': 'USD',
            'Action': 'BUY'
        }
        is_valid, error = validate_transaction_data(transaction)
        assert is_valid is False
        assert "Invalid ISIN format" in error
    
    def test_validate_transaction_data_invalid_quantity(self):
        """Test transaction with invalid quantity."""
        transaction = {
            'ISIN': 'US0378331005',
            'Quantity': -10.0,
            'Price': 150.0,
            'Currency': 'USD',
            'Action': 'BUY'
        }
        is_valid, error = validate_transaction_data(transaction)
        assert is_valid is False
        assert "Quantity must be positive" in error
