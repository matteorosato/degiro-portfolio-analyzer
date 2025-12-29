"""Business logic for transactions domain."""
import pandas as pd
import json
import warnings
from pathlib import Path
from typing import Optional, Dict
import yfinance as yf
import os

from backend.app.core.config import config
from backend.app.shared.logger import app_logger
from .validators import validate_isin, validate_transaction_data

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)


class TransactionService:
    """Service for managing financial transactions."""
    
    def __init__(self):
        """Initialize transaction service with file paths."""
        self.csv_path = Path(config.TRANSACTION_CSV)
        self.mapping_path = Path(config.ISIN_MAPPING)
        # Exchange mapping from DeGiro to Yahoo Finance
        self.degiro_to_yf_exchange = {
            "EAM": "AMS",
            "XET": "GER",
            "MIL": "MIL",
            "LSE": "LSE",
            "NDQ": "NYQ",
            "NSY": "SWX",
        }
    
    def get_all_transactions(self) -> pd.DataFrame:
        """
        Load and process all transactions from CSV file.
        
        Workflow: load_data() → map_isin() → prepare_data()
        
        Returns:
            DataFrame with processed transactions
        """
        try:
            app_logger.info("[TRANSACTIONS] Processing transactions...")
            
            # Step 1: Load raw data from CSV
            raw_df = self._load_data()
            
            if raw_df.empty:
                app_logger.warning("[TRANSACTIONS] No transaction data found")
                return pd.DataFrame()
            
            # Step 2: Update ISIN mapping and apply ticker mapping
            mapped_df = self._map_isin(raw_df)
            
            # Step 3: Clean and transform the data
            transactions_df = self._prepare_data(mapped_df)
            
            app_logger.info(f"[TRANSACTIONS] Processed {len(transactions_df)} transactions successfully")
            
            return transactions_df.copy()
            
        except Exception as e:
            app_logger.error(f"[TRANSACTIONS] Error processing transactions: {e}", exc_info=True)
            raise
    
    def get_filtered_transactions(
        self,
        isin: Optional[str] = None,
        stock: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get transactions with filters applied.
        
        Args:
            isin: Filter by ISIN code
            stock: Filter by ticker symbol
            action: Filter by action (BUY/SELL)
            start_date: Filter from date (YYYY-MM-DD)
            end_date: Filter to date (YYYY-MM-DD)
            
        Returns:
            Filtered DataFrame
        """
        df = self.get_all_transactions()
        
        if df.empty:
            return df
        
        # Apply filters
        if isin:
            df = df[df['ISIN'] == isin]
        
        if stock:
            df = df[df['Stock'] == stock]
        
        if action:
            df = df[df['Action'] == action]
        
        if start_date:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        
        if end_date:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        app_logger.info(f"[TRANSACTIONS] Filtered to {len(df)} transactions")
        return df
    
    def get_transaction_stats(self) -> Dict:
        """
        Calculate statistics about transactions.
        
        Returns:
            Dictionary with statistics
        """
        df = self.get_all_transactions()
        
        if df.empty:
            return {
                "total_transactions": 0,
                "total_buys": 0,
                "total_sells": 0,
                "unique_stocks": 0,
                "date_range": {},
                "total_invested": 0.0,
                "total_fees": 0.0
            }
        
        df['Date'] = pd.to_datetime(df['Date'])
        
        return {
            "total_transactions": len(df),
            "total_buys": len(df[df['Action'] == 'BUY']),
            "total_sells": len(df[df['Action'] == 'SELL']),
            "unique_stocks": df['Stock'].nunique(),
            "date_range": {
                "start": df['Date'].min().strftime('%Y-%m-%d'),
                "end": df['Date'].max().strftime('%Y-%m-%d')
            },
            "total_invested": float(df[df['Action'] == 'BUY']['Cost'].sum()),
            "total_fees": float(df['Transaction_costs'].sum())
        }
    
    def _load_data(self) -> pd.DataFrame:
        """
        Load transactions from CSV and perform basic column mapping.
        
        Returns:
            Raw transaction data with standardized column names
        """
        if not self.csv_path.exists():
            app_logger.warning(f"[TRANSACTIONS] File not found: {self.csv_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(self.csv_path)
            
            column_names = {
                0: 'Date',
                1: 'Time',
                2: 'Product',
                3: 'ISIN',
                4: 'Reference',
                5: 'Venue',
                6: 'Quantity',
                7: 'Price',
                8: 'Price_Currency',
                9: 'Local_Value',
                10: 'Local_Value_Currency',
                11: 'Value',
                12: 'Value_Currency',
                13: 'Exchange_Rate',
                14: 'Transaction_Costs',
                15: 'Transaction_Costs_Currency',
                16: 'Total',
                17: 'Total_Currency',
                18: 'Order_ID'
            }
            
            # Apply column mapping
            column_indices = list(column_names.keys())
            df = df.iloc[:, column_indices]
            df.columns = list(column_names.values())
            
            # Rename for mapping
            df.rename(
                columns={
                    "Product": "Product_Name_DeGiro",
                    "Reference": "Exchange",
                    "Total_Currency": "Currency",
                },
                inplace=True
            )
            
            return df
            
        except Exception as e:
            app_logger.error(f"[TRANSACTIONS] Error loading CSV: {e}", exc_info=True)
            return pd.DataFrame()
    
    def _map_isin(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Update ISIN mapping file and apply ticker mapping to DataFrame.
        
        Args:
            df: Raw transaction DataFrame
            
        Returns:
            DataFrame with Stock and Product columns added
        """
        if df.empty:
            return df
        
        try:
            app_logger.info("[ISIN-MAPPING] Updating ISIN mapping...")
            
            # Update mapping file
            isin_mapping = self._update_isin_mapping(df)
            
            # Apply mapping to DataFrame
            if isin_mapping:
                df['Stock'] = df['ISIN'].apply(
                    lambda isin: isin_mapping.get(isin, {}).get("ticker", "")
                ).astype(str)
                df['Product'] = df['ISIN'].apply(
                    lambda isin: isin_mapping.get(isin, {}).get("display_name", "")
                ).astype(str)
            else:
                df['Stock'] = ''
                df['Product'] = ''
            
            app_logger.info("[ISIN-MAPPING] Mapping applied successfully")
            return df
            
        except Exception as e:
            app_logger.error(f"[ISIN-MAPPING] Error: {e}", exc_info=True)
            df['Stock'] = ''
            df['Product'] = ''
            return df
    
    def _update_isin_mapping(self, df: pd.DataFrame) -> Dict:
        """
        Update ISIN to ticker mapping JSON file.
        
        Args:
            df: Transaction DataFrame
            
        Returns:
            Updated mapping dictionary
        """
        required_cols = {'ISIN', 'Product_Name_DeGiro', 'Exchange'}
        if not required_cols.issubset(df.columns):
            app_logger.warning("[ISIN-MAPPING] Required columns missing")
            return {}
        
        # Load existing mapping
        try:
            if self.mapping_path.exists():
                with open(self.mapping_path, 'r') as f:
                    existing_mapping = json.load(f)
            else:
                existing_mapping = {}
        except (FileNotFoundError, json.JSONDecodeError):
            existing_mapping = {}
        
        # Find unique ISINs
        isin_list = df[['ISIN', 'Product_Name_DeGiro', 'Exchange']].drop_duplicates()
        isin_list = isin_list[
            isin_list['ISIN'].notna() & (isin_list['ISIN'].astype(str).str.strip() != "")
        ]
        
        # Add new ISINs
        for isin, name, exchange in isin_list.values:
            if isin not in existing_mapping:
                try:
                    product = self._get_yahoo_product(
                        isin=isin,
                        exchange=self.degiro_to_yf_exchange.get(exchange)
                    )
                except Exception:
                    product = {}
                
                app_logger.info(f"[ISIN-MAPPING] Adding {isin} -> {name}")
                existing_mapping[isin] = {
                    "ticker": product.get("symbol", ""),
                    "degiro_name": name,
                    "display_name": product.get("shortname", name),
                    "exchange": exchange,
                    "product_type": product.get("quoteType", "")
                }
        
        # Ensure FULL_PORTFOLIO entry exists
        if "FULL_PORTFOLIO" not in existing_mapping:
            existing_mapping["FULL_PORTFOLIO"] = {
                "ticker": "FULL",
                "degiro_name": "Full portfolio",
                "display_name": "Full portfolio",
                "exchange": "",
                "product_type": ""
            }
        
        # Save updated mapping
        self.mapping_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.mapping_path, 'w') as f:
            json.dump(existing_mapping, f, indent=4)
        
        return existing_mapping
    
    def _get_yahoo_product(self, isin: str, exchange: Optional[str] = None) -> dict:
        """
        Retrieve product information from Yahoo Finance using ISIN.
        
        Args:
            isin: ISIN code
            exchange: Exchange code (Yahoo Finance format)
            
        Returns:
            Product information dictionary
        """
        results_by_isin = yf.Search(isin, max_results=1)
        if not results_by_isin.quotes:
            return {}
        
        product_long_name = results_by_isin.quotes[0].get('longname')
        if not product_long_name:
            return {}
        
        results_by_product_name = yf.Search(product_long_name, max_results=20)
        if not results_by_product_name.quotes or not exchange:
            return {}
        
        # Search for product with desired exchange
        for quote in results_by_product_name.quotes:
            if quote.get('exchange') == exchange:
                return quote
        
        return {}
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and transform transaction data.
        
        Args:
            df: Transaction DataFrame from _map_isin()
            
        Returns:
            Cleaned and processed transaction data
        """
        if df.empty:
            return df
        
        try:
            # Determine action (BUY/SELL)
            df['Action'] = df['Quantity'].apply(lambda x: 'BUY' if x > 0 else 'SELL')
            
            # Parse dates and times
            df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
            df['Time'] = pd.to_datetime(df['Time'], format='%H:%M').dt.time
            
            # Convert numeric columns (comma as decimal separator)
            df['Quantity'] = (
                df['Quantity']
                .fillna("0")
                .astype(str)
                .str.replace(",", ".")
                .astype(float)
            )
            
            df['Price'] = (
                df['Price']
                .fillna("0")
                .astype(str)
                .str.replace(",", ".")
                .astype(float)
            )
            
            df['Cost'] = (
                df['Value']
                .fillna("0")
                .astype(str)
                .str.replace(",", ".")
                .astype(float)
            )
            
            df['Transaction_costs'] = (
                df['Transaction_Costs']
                .fillna("0")
                .astype(str)
                .str.replace(",", ".")
                .astype(float)
            )
            
            # Sort chronologically
            df = df.sort_values(by=["Date", "Time"]).reset_index(drop=True)
            
            return df
            
        except Exception as e:
            app_logger.error(f"[TRANSACTIONS] Error preparing data: {e}", exc_info=True)
            return pd.DataFrame()


# Singleton instance
transaction_service = TransactionService()


# Convenience function for backward compatibility
def get_transactions() -> pd.DataFrame:
    """Get all transactions (backward compatible with old code)."""
    return transaction_service.get_all_transactions()
