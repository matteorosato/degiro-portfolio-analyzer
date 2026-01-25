"""Unit tests for portfolio analyzer."""
import pytest
import pandas as pd
from datetime import datetime, date
from unittest.mock import Mock, patch, mock_open
from backend.app.routers.portfolio.analyzer import PortfolioAnalyzer
from backend.app.routers.portfolio.exceptions import InvalidTransactionError


class TestPortfolioAnalyzer:
    """Test suite for PortfolioAnalyzer class."""
    
    @pytest.fixture
    def sample_transactions(self):
        """Create sample transaction data for testing."""
        return pd.DataFrame({
            'Date': pd.to_datetime(['2023-01-01', '2023-01-15', '2023-02-01']),
            'Time': ['10:00:00', '11:00:00', '12:00:00'],
            'Stock': ['AAPL', 'AAPL', 'AAPL'],
            'Action': ['BUY', 'BUY', 'SELL'],
            'Quantity': [10, 5, 3],
            'Cost': [-1000, -500, 360],
            'Transaction_costs': [-1.50, -1.00, -0.75],
            'Currency': ['USD', 'USD', 'USD']
        })
    
    @pytest.fixture
    def analyzer(self, sample_transactions):
        """Create PortfolioAnalyzer instance with sample data."""
        return PortfolioAnalyzer(sample_transactions)
    
    def test_init(self, sample_transactions):
        """Test analyzer initialization."""
        analyzer = PortfolioAnalyzer(sample_transactions)
        assert isinstance(analyzer.transactions, pd.DataFrame)
        assert len(analyzer.transactions) == 3
        assert analyzer._isin_mapping is None  # Cache should be empty initially
    
    def test_clear_cache(self, analyzer):
        """Test clearing the ISIN mapping cache."""
        # Set a dummy cache
        analyzer._isin_mapping = {"test": "data"}
        assert analyzer._isin_mapping is not None
        
        # Clear and verify
        analyzer.clear_cache()
        assert analyzer._isin_mapping is None
    
    @patch('yfinance.download')
    def test_get_price_at_date_single_ticker(self, mock_yf, analyzer):
        """Test fetching price for a single ticker."""
        # Mock yfinance response for single ticker
        mock_data = pd.Series(
            [150.0, 151.0, 152.0],
            index=pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03'])
        )
        mock_yf.return_value = {"Close": mock_data}
        
        result = analyzer.get_price_at_date(['AAPL'], '2023-01-01', '2023-01-03')
        
        assert '2023-01-01' in result
        assert '2023-01-02' in result
        assert result['2023-01-01'] == 150.0
    
    @patch('yfinance.download')
    def test_get_price_at_date_multiple_tickers(self, mock_yf, analyzer):
        """Test fetching prices for multiple tickers."""
        # Mock yfinance response for multiple tickers
        mock_data = pd.DataFrame({
            'AAPL': [150.0, 151.0],
            'MSFT': [250.0, 251.0]
        }, index=pd.to_datetime(['2023-01-01', '2023-01-02']))
        
        mock_yf.return_value = {"Close": mock_data}
        
        result = analyzer.get_price_at_date(['AAPL', 'MSFT'], '2023-01-01', '2023-01-02')
        
        assert 'AAPL' in result
        assert 'MSFT' in result
        assert result['AAPL']['2023-01-01'] == 150.0
        assert result['MSFT']['2023-01-01'] == 250.0
    
    def test_get_first_last_open_day_first(self, analyzer):
        """Test getting first open market day."""
        stock_price_data = {
            '2023-01-02': 150.0,
            '2023-01-03': 151.0,
            '2023-01-04': 152.0
        }
        
        result = analyzer.get_first_last_open_day(
            datetime(2023, 1, 1),
            datetime(2023, 1, 5),
            stock_price_data,
            first=True
        )
        
        assert result == '2023-01-02'
    
    def test_get_first_last_open_day_last(self, analyzer):
        """Test getting last open market day."""
        stock_price_data = {
            '2023-01-02': 150.0,
            '2023-01-03': 151.0,
            '2023-01-04': 152.0
        }
        
        result = analyzer.get_first_last_open_day(
            datetime(2023, 1, 1),
            datetime(2023, 1, 5),
            stock_price_data,
            first=False
        )
        
        assert result == '2023-01-04'
    
    def test_get_first_last_open_day_no_data(self, analyzer):
        """Test getting first/last day when no data available."""
        stock_price_data = {}
        
        result = analyzer.get_first_last_open_day(
            datetime(2023, 1, 1),
            datetime(2023, 1, 5),
            stock_price_data,
            first=True
        )
        
        assert result == '2023-01-01'
    
    @patch('yfinance.download')
    def test_get_fx_rate(self, mock_yf, analyzer):
        """Test FX rate fetching."""
        # Mock yfinance FX data
        mock_data = pd.DataFrame({
            'Close': pd.Series([0.85, 0.86], index=pd.to_datetime(['2023-01-01', '2023-01-02']))
        })
        mock_yf.return_value = mock_data
        
        result = analyzer.get_fx_rate('USD', 'EUR', '2023-01-01', '2023-01-02')
        
        assert '2023-01-01' in result
        assert result['2023-01-01'] == 0.85
    
    @patch('yfinance.download')
    def test_get_fx_rate_empty_data(self, mock_yf, analyzer):
        """Test FX rate with empty response."""
        mock_yf.return_value = pd.DataFrame()
        
        result = analyzer.get_fx_rate('USD', 'EUR', '2023-01-01', '2023-01-02')
        
        assert result == {}
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"US1234567890": {"ticker": "AAPL", "display_name": "Apple Inc."}}')
    def test_calculate_mwr(self, mock_file, analyzer):
        """Test Money Weighted Return calculation."""
        stock_price_data = {
            '2023-01-01': 100.0,
            '2023-01-15': 105.0,
            '2023-02-01': 110.0,
            '2023-02-02': 115.0
        }
        
        result = analyzer.calculate_mwr(
            'AAPL',
            '2023-01-01',
            '2023-02-01',
            stock_price_data
        )
        
        # Verify result structure
        assert 'ticker' in result
        assert 'quantity' in result
        assert 'avg_cost' in result
        assert 'current_value' in result
        assert 'net_return' in result
        assert result['ticker'] == 'AAPL'
        assert isinstance(result['quantity'], int)
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"US1234567890": {"ticker": "AAPL", "display_name": "Apple Inc."}}')
    def test_calculate_total_portfolio_performance(self, mock_file, analyzer):
        """Test total portfolio performance aggregation."""
        stock_results = {
            'AAPL': {
                'quantity': 10,
                'total_cost': 1000,
                'transaction_costs': 5,
                'current_value': 1200,
                'current_money_weighted_return': 200,
                'realized_return': 50,
                'net_return': 250
            },
            'MSFT': {
                'quantity': 5,
                'total_cost': 500,
                'transaction_costs': 2,
                'current_value': 550,
                'current_money_weighted_return': 50,
                'realized_return': 20,
                'net_return': 70
            }
        }
        
        result = analyzer.calculate_total_portfolio_performance(
            '2023-01-01',
            '2023-02-01',
            stock_results
        )
        
        assert result['ticker'] == 'FULL'
        assert result['product'] == 'Full portfolio'
        assert result['quantity'] == 15
        assert result['total_cost'] == 1500
        assert result['transaction_costs'] == 7
        assert result['current_value'] == 1750
        assert result['current_money_weighted_return'] == 250
        assert result['realized_return'] == 70
        assert result['net_return'] == 320
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"US1234567890": {"ticker": "AAPL", "display_name": "Apple Inc."}}')
    def test_calculate_all_stocks_mwr(self, mock_file, analyzer):
        """Test MWR calculation for all stocks."""
        stock_prices = {
            'AAPL': {
                '2023-01-01': 100.0,
                '2023-02-01': 110.0
            }
        }
        
        result = analyzer.calculate_all_stocks_mwr(
            ['AAPL'],
            '2023-01-01',
            '2023-02-01',
            stock_prices
        )
        
        assert 'AAPL' in result
        assert 'portfolio' in result
        assert result['portfolio']['ticker'] == 'FULL'
    
    def test_calculate_mwr_with_no_holdings(self, analyzer):
        """Test MWR calculation when no stock is held."""
        # Create transactions with buy and sell all
        transactions = pd.DataFrame({
            'Date': pd.to_datetime(['2023-01-01', '2023-01-15']),
            'Time': ['10:00:00', '11:00:00'],
            'Stock': ['AAPL', 'AAPL'],
            'Action': ['BUY', 'SELL'],
            'Quantity': [10, 10],
            'Cost': [-1000, 1100],
            'Transaction_costs': [-1.50, -1.00]
        })
        
        analyzer_empty = PortfolioAnalyzer(transactions)
        
        stock_price_data = {
            '2023-01-01': 100.0,
            '2023-01-15': 110.0,
            '2023-02-01': 115.0
        }
        
        with patch('builtins.open', mock_open(read_data='{"US1234567890": {"ticker": "AAPL", "display_name": "Apple Inc."}}')):
            result = analyzer_empty.calculate_mwr(
                'AAPL',
                '2023-01-01',
                '2023-02-01',
                stock_price_data
            )
        
        assert result['quantity'] == 0
        assert result['current_money_weighted_return'] == 0
