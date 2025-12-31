"""Portfolio service - main calculation and data management logic."""
import os
from datetime import datetime, timedelta
import pandas as pd
import json
import warnings
import time
from backend.app.shared.logger import app_logger
from backend.app.routers.transactions.services import transaction_service
from backend.app.routers.portfolio.analyzer import PortfolioAnalyzer
from backend.app.config import config

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)


class PortfolioService:
    """Service for portfolio calculation and management."""
    
    def calc_portfolio(self) -> None:
        """Calculate portfolio performance for all days from first transaction to today.
        
        This method:
        1. Loads transaction data
        2. Fetches historical stock prices
        3. Converts all prices to EUR
        4. Calculates daily portfolio performance
        5. Saves results to Parquet files (daily and monthly)
        
        Raises:
            Exception: If portfolio calculation fails
        """
        app_logger.info("[PORTFOLIO-CALC] Starting portfolio calculation...")

        try:
            # Start timing
            start_time = time.time()

            # Get the transactions DataFrame from the service
            transactions_df = transaction_service.get_all_transactions()
            app_logger.info(
                f"[PORTFOLIO-CALC] Retrieved transactions DataFrame with {len(transactions_df)} rows."
            )
            
            # Instantiate the analyzer with the transaction data
            analyzer = PortfolioAnalyzer(transactions_df)

            if transactions_df.empty:
                app_logger.warning("[PORTFOLIO-CALC] No transactions found. Skipping portfolio calculation.")
                return
            
            app_logger.info("[PORTFOLIO-CALC] Retrieving portfolio data...")
            
            # Fix data types and definitions
            transactions = transactions_df[
                transactions_df["Stock"].notna() & (transactions_df["Stock"] != '')
            ]
            if transactions.empty:
                app_logger.warning(
                    "[PORTFOLIO-CALC] No valid transactions with a stock ticker. Skipping portfolio calculation."
                )
                return
            
            transactions["Date"] = pd.to_datetime(transactions["Date"])
            start_date = transactions['Date'].min()
            today = datetime.today()
            end_dates = pd.date_range(start=start_date, end=today, freq='D')[1:]  # Exclude the start_date

            app_logger.info(
                f"[PORTFOLIO-CALC] Processing portfolio performance from "
                f"{start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
            )

            # Initialize an empty list to store portfolio data for each day
            portfolio_results_list = []

            # Get recent stock price data for new end_dates
            stock_list = transactions["Stock"].unique().tolist()  # All stocks

            yf_start_date = start_date if len(end_dates) > 30 else (today - timedelta(days=30))
            yf_stock_price_data = analyzer.get_price_at_date(
                stock_list, 
                yf_start_date.strftime('%Y-%m-%d'), 
                (today + timedelta(days=1)).strftime('%Y-%m-%d')
            )
        
            # Update stock prices to EUR
            # Remove duplicates and create ticker-to-currency dict
            ticker_currency_dict = transactions.drop_duplicates(subset=['Stock', 'Price_Currency'])\
                                            .set_index('Stock')['Price_Currency'].to_dict()

            # Group tickers by currency (excluding EUR)
            currency_ticker_map = {}
            for ticker, currency in ticker_currency_dict.items():
                if currency != 'EUR':
                    currency_ticker_map.setdefault(currency, []).append(ticker)

            # Fetch FX rates once per currency
            fx_rates_by_currency = {}
            for currency in currency_ticker_map:
                fx_rates_by_currency[currency] = analyzer.get_fx_rate(
                    currency, 'EUR',
                    yf_start_date.strftime('%Y-%m-%d'),
                    (today + timedelta(days=1)).strftime('%Y-%m-%d')
                )

            # Apply FX rates to stock prices
            for currency, tickers in currency_ticker_map.items():
                fx_rate = fx_rates_by_currency.get(currency)
                if fx_rate is None:
                    continue
                for ticker in tickers:
                    prices = yf_stock_price_data.get(ticker, {})
                    for date, price in prices.items():
                        prices[date] = price * fx_rate.get(date, 1)
            
            # Load existing results from Parquet file
            try:
                portfolio_results_df = pd.read_parquet(config.PORTFOLIO_DAILY)
                app_logger.info("[PORTFOLIO-CALC] Loaded portfolio_performance_daily from Parquet")

                # Remove last 2 days to force refresh (get end of day data)
                last_2_days = sorted(portfolio_results_df['end_date'].unique())[-2:]
                portfolio_results_df = portfolio_results_df[
                    ~portfolio_results_df['end_date'].isin(last_2_days)
                ]

            except Exception as e:
                app_logger.warning(
                    f"[PORTFOLIO-CALC] Failed to load portfolio_performance_daily from Parquet: {e}"
                )
                portfolio_results_df = pd.DataFrame(
                    columns=['product', 'ticker', 'quantity', 'start_date', 'end_date', 
                            'avg_cost', 'total_cost', 'transaction_costs', 'current_value', 
                            'current_money_weighted_return', 'realized_return', 
                            'net_return', 'current_performance_percentage', 
                            'net_performance_percentage']
                )
            
            # Load stock prices from Parquet file
            try:
                stock_prices_df = pd.read_parquet(config.STOCK_PRICES)
                stock_prices_df = stock_prices_df.dropna(subset=['price'])
                stock_prices_dict = (
                    stock_prices_df.groupby('ticker')
                    .apply(lambda x: x.set_index('date')['price'].to_dict())
                    .to_dict()
                )
                app_logger.info("[PORTFOLIO-CALC] Loaded stock_prices from Parquet")
            except Exception as e:
                app_logger.warning(f"[PORTFOLIO-CALC] Failed to load stock_prices from Parquet: {e}")
                stock_prices_dict = {}

            # Append fresh stock price data to stock_prices_dict
            for ticker, prices in yf_stock_price_data.items():
                if ticker in stock_prices_dict:
                    stock_prices_dict[ticker].update(prices)
                else:
                    stock_prices_dict[ticker] = prices

            # Remove duplicates from stock_prices_dict
            for ticker in stock_prices_dict:
                stock_prices_dict[ticker] = {
                    date: price 
                    for date, price in sorted(stock_prices_dict[ticker].items())
                }

            # Loop over each end date, calculate portfolio results, and add to the list
            for end_date in end_dates:
                # Try to get end_date data, else continue
                try:
                    # Format end date to string for comparison
                    end_date_str = end_date.strftime('%Y-%m-%d')

                    # Skip weekends (Saturday and Sunday)
                    if end_date.weekday() >= 5:
                        continue  # Skip this iteration if it's a weekend
                    
                    # Check if the result for this end date already exists in the DataFrame
                    if not portfolio_results_df[portfolio_results_df['end_date'] == end_date_str].empty:
                        continue  # Skip if already present

                    app_logger.info(f"[PORTFOLIO-CALC] Retrieving data for: {end_date_str}")

                    # Ensure that the transactions before the end date are not empty
                    transactions_before_end = transactions[
                        transactions["Date"].apply(
                            lambda x: x.strftime('%Y-%m-%d') if isinstance(x, datetime) else x
                        ) <= end_date_str
                    ]

                    if transactions_before_end.empty:
                        app_logger.info(
                            f"[PORTFOLIO-CALC] No transactions found for date: {end_date_str}. Skipping..."
                        )
                        continue

                    stock_list = list(transactions_before_end["Stock"].unique())
                    
                    # Retrieve stock results using analyzer class
                    result = analyzer.calculate_all_stocks_mwr(
                        start_date=start_date.strftime('%Y-%m-%d'), 
                        end_date=end_date_str, 
                        stocks=stock_list,
                        stock_prices=stock_prices_dict
                    )
                    
                    for key in result:
                        portfolio_data = result.get(key)
                        
                        # Check if portfolio_data is valid before proceeding
                        if portfolio_data is None or not isinstance(portfolio_data, dict):
                            app_logger.warning(
                                f"[PORTFOLIO-CALC] Stock data is missing or invalid for date: "
                                f"{end_date_str}. Result: {result}"
                            )
                            continue
                        
                        # Ensure end_date is included in the portfolio_data
                        portfolio_data['end_date'] = end_date_str
                        
                        # Append the new data to the list
                        portfolio_results_list.append(portfolio_data)

                except Exception as e:
                    app_logger.warning(f"[PORTFOLIO-CALC] Failed to retrieve daily data for {end_date}: {e}")
                    continue

            # Combine the list into a DataFrame if there are new results
            if portfolio_results_list:
                new_portfolio_results_df = pd.DataFrame(portfolio_results_list)
                # Append new results to the existing DataFrame
                portfolio_results_df = pd.concat(
                    [portfolio_results_df, new_portfolio_results_df], 
                    ignore_index=True
                )

            # Save the updated DataFrame to a Parquet file
            portfolio_results_df = portfolio_results_df.dropna()
            portfolio_results_df['quantity'] = portfolio_results_df['quantity'].astype(int)

            # Update product column based on ISIN mapping json
            with open(config.ISIN_MAPPING, 'r') as f:
                isin_mapping = json.load(f)

            # Build a reverse map: ticker -> display_name
            ticker_to_name = {
                data.get("ticker"): data.get("display_name", "")
                for data in isin_mapping.values()
                if "ticker" in data
            }

            portfolio_results_df['product'] = portfolio_results_df['ticker'].map(ticker_to_name).fillna('')

            # Store parquet files
            # Daily table
            portfolio_results_df.to_parquet(config.PORTFOLIO_DAILY, index=False)

            # Stock prices
            stock_prices_records = []
            for ticker, date_prices in stock_prices_dict.items():
                currency = ticker_currency_dict.get(ticker, 'EUR')  # Default EUR if missing
                fx_rate_data = fx_rates_by_currency.get(currency, {}) if currency != 'EUR' else {}

                currency_pair = f"{currency}-EUR" if currency != 'EUR' else "EUR-EUR"

                for date, price in date_prices.items():
                    # FX rate for the date if not EUR, else 1
                    fx_rate = fx_rate_data.get(date, 1) if currency != 'EUR' else 1

                    stock_prices_records.append({
                        "ticker": ticker,
                        "date": date,
                        "price": price if price is not None else 0,
                        "fx_rate": fx_rate,
                        "currency_pair": currency_pair
                    })

            stock_prices_df = pd.DataFrame(stock_prices_records)
            stock_prices_df = stock_prices_df.dropna(subset=['price'])
            stock_prices_df.to_parquet(config.STOCK_PRICES, index=False)

            app_logger.info("[PORTFOLIO-CALC] Daily output saved locally")
            
            # End timing
            end_time = time.time()
            execution_time = round(end_time - start_time, 2)
            app_logger.info(f"[PORTFOLIO-CALC] Execution time: {execution_time} seconds")
            app_logger.info(f"[PORTFOLIO-CALC] Portfolio calculation completed successfully ({execution_time}s)")
        
        except Exception as e:
            app_logger.error(f"[PORTFOLIO-CALC] Error during portfolio calculation: {e}", exc_info=True)
            raise e


# Singleton instance
portfolio_service = PortfolioService()
