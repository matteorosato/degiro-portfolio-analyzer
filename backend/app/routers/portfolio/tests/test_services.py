"""Unit tests for portfolio services."""
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from backend.app.routers.portfolio.services import PortfolioService


class TestPortfolioService:
    """Test suite for PortfolioService class."""
    
    @pytest.fixture
    def service(self):
        """Create PortfolioService instance."""
        return PortfolioService()
    
    @pytest.fixture
    def sample_transactions(self):
        """Create sample transaction DataFrame."""
        return pd.DataFrame({
            'Date': pd.to_datetime(['2023-01-01', '2023-01-15']),
            'Time': ['10:00:00', '11:00:00'],
            'Stock': ['AAPL', 'AAPL'],
            'Action': ['BUY', 'BUY'],
            'Quantity': [10, 5],
            'Cost': [-1000, -500],
            'Transaction_costs': [-1.50, -1.00],
            'Currency': ['USD', 'USD']
        })
    
    @patch('backend.app.routers.portfolio.services.transaction_service')
    @patch('backend.app.routers.portfolio.services.PortfolioAnalyzer')
    @patch('builtins.open')
    @patch('pandas.read_parquet')
    @patch('pandas.DataFrame.to_parquet')
    def test_calc_portfolio_success(
        self, 
        mock_to_parquet, 
        mock_read_parquet, 
        mock_open_file,
        mock_analyzer_class,
        mock_transaction_service,
        service,
        sample_transactions
    ):
        """Test successful portfolio calculation."""
        # Mock transaction service
        mock_transaction_service.get_all_transactions.return_value = sample_transactions
        
        # Mock analyzer instance
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        
        # Mock stock price data
        mock_analyzer.get_price_at_date.return_value = {
            'AAPL': {
                '2023-01-01': 100.0,
                '2023-01-15': 105.0
            }
        }
        
        # Mock FX rates (empty since we're using USD)
        mock_analyzer.get_fx_rate.return_value = {}
        
        # Mock analyzer results
        mock_analyzer.calculate_all_stocks_mwr.return_value = {
            'AAPL': {
                'product': 'Apple Inc.',
                'ticker': 'AAPL',
                'quantity': 15,
                'start_date': '2023-01-01',
                'end_date': '2023-01-15',
                'avg_cost': 100.0,
                'total_cost': 1500.0,
                'transaction_costs': 2.5,
                'current_value': 1575.0,
                'current_money_weighted_return': 75.0,
                'realized_return': 0.0,
                'net_return': 75.0,
                'current_performance_percentage': 5.0,
                'net_performance_percentage': 5.0
            },
            'portfolio': {
                'product': 'Full portfolio',
                'ticker': 'FULL',
                'quantity': 15,
                'start_date': '2023-01-01',
                'end_date': '2023-01-15',
                'avg_cost': 100.0,
                'total_cost': 1500.0,
                'transaction_costs': 2.5,
                'current_value': 1575.0,
                'current_money_weighted_return': 75.0,
                'realized_return': 0.0,
                'net_return': 75.0,
                'current_performance_percentage': 5.0,
                'net_performance_percentage': 5.0
            }
        }
        
        # Mock ISIN mapping
        mock_open_file.return_value.__enter__.return_value.read.return_value = (
            '{"US1234567890": {"ticker": "AAPL", "display_name": "Apple Inc."}}'
        )
        
        # Mock existing parquet data (empty DataFrame)
        mock_read_parquet.side_effect = Exception("File not found")
        
        # Execute
        service.calc_portfolio()
        
        # Verify transaction service was called
        mock_transaction_service.get_all_transactions.assert_called_once()
        
        # Verify parquet files were saved
        assert mock_to_parquet.called
    
    @patch('backend.app.routers.portfolio.services.transaction_service')
    def test_calc_portfolio_empty_transactions(self, mock_transaction_service, service):
        """Test portfolio calculation with empty transactions."""
        mock_transaction_service.get_all_transactions.return_value = pd.DataFrame()
        
        # Should complete without error
        service.calc_portfolio()
        
        mock_transaction_service.get_all_transactions.assert_called_once()
    
    @patch('backend.app.routers.portfolio.services.transaction_service')
    def test_calc_portfolio_no_valid_stocks(self, mock_transaction_service, service):
        """Test portfolio calculation with no valid stock tickers."""
        # Create transactions without stock tickers
        invalid_transactions = pd.DataFrame({
            'Date': pd.to_datetime(['2023-01-01']),
            'Time': ['10:00:00'],
            'Stock': [None],
            'Action': ['BUY'],
            'Quantity': [10],
            'Cost': [-1000],
            'Transaction_costs': [-1.50],
            'Currency': ['USD']
        })
        
        mock_transaction_service.get_all_transactions.return_value = invalid_transactions
        
        # Should complete without error
        service.calc_portfolio()
        
        mock_transaction_service.get_all_transactions.assert_called_once()
    
    @patch('backend.app.routers.portfolio.services.transaction_service')
    @patch('backend.app.routers.portfolio.services.PortfolioAnalyzer')
    def test_calc_portfolio_with_exception(
        self, 
        mock_analyzer_class,
        mock_transaction_service,
        service,
        sample_transactions
    ):
        """Test portfolio calculation error handling."""
        mock_transaction_service.get_all_transactions.return_value = sample_transactions
        
        # Mock analyzer to raise exception
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.get_price_at_date.side_effect = Exception("API Error")
        
        # Should raise exception
        with pytest.raises(Exception, match="API Error"):
            service.calc_portfolio()
    
    @patch('backend.app.routers.portfolio.services.transaction_service')
    @patch('backend.app.routers.portfolio.services.PortfolioAnalyzer')
    @patch('builtins.open')
    @patch('pandas.read_parquet')
    def test_calc_portfolio_loads_existing_data(
        self,
        mock_read_parquet,
        mock_open_file,
        mock_analyzer_class,
        mock_transaction_service,
        service,
        sample_transactions
    ):
        """Test that existing parquet data is loaded and updated."""
        mock_transaction_service.get_all_transactions.return_value = sample_transactions
        
        # Mock existing portfolio data
        existing_data = pd.DataFrame({
            'product': ['Apple Inc.'],
            'ticker': ['AAPL'],
            'quantity': [10],
            'start_date': ['2023-01-01'],
            'end_date': ['2023-01-10'],
            'avg_cost': [100.0],
            'total_cost': [1000.0],
            'transaction_costs': [1.5],
            'current_value': [1050.0],
            'current_money_weighted_return': [50.0],
            'realized_return': [0.0],
            'net_return': [50.0],
            'current_performance_percentage': [5.0],
            'net_performance_percentage': [5.0]
        })
        
        mock_read_parquet.return_value = existing_data
        
        # Mock analyzer
        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.get_price_at_date.return_value = {'AAPL': {'2023-01-01': 100.0}}
        mock_analyzer.get_fx_rate.return_value = {}
        mock_analyzer.calculate_all_stocks_mwr.return_value = {
            'AAPL': {
                'product': 'Apple Inc.',
                'ticker': 'AAPL',
                'quantity': 15,
                'start_date': '2023-01-01',
                'end_date': '2023-01-15',
                'avg_cost': 100.0,
                'total_cost': 1500.0,
                'transaction_costs': 2.5,
                'current_value': 1575.0,
                'current_money_weighted_return': 75.0,
                'realized_return': 0.0,
                'net_return': 75.0,
                'current_performance_percentage': 5.0,
                'net_performance_percentage': 5.0
            },
            'portfolio': {
                'product': 'Full portfolio',
                'ticker': 'FULL',
                'quantity': 15,
                'start_date': '2023-01-01',
                'end_date': '2023-01-15',
                'avg_cost': 100.0,
                'total_cost': 1500.0,
                'transaction_costs': 2.5,
                'current_value': 1575.0,
                'current_money_weighted_return': 75.0,
                'realized_return': 0.0,
                'net_return': 75.0,
                'current_performance_percentage': 5.0,
                'net_performance_percentage': 5.0
            }
        }
        
        # Mock file operations
        mock_open_file.return_value.__enter__.return_value.read.return_value = (
            '{"US1234567890": {"ticker": "AAPL", "display_name": "Apple Inc."}}'
        )
        
        # Verify existing data was loaded
        mock_read_parquet.assert_called()
