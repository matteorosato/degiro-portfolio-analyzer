"""Business logic for transactions domain."""
import pandas as pd
import json
import warnings
from pathlib import Path
from typing import Optional, Dict
import yfinance as yf

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
            
        Raises:
            FileNotFoundError: If transaction CSV file does not exist
        """
        if not self.csv_path.exists():
            error_msg = f"Transaction CSV file not found: {self.csv_path}"
            app_logger.error(f"[TRANSACTIONS] {error_msg}")
            raise FileNotFoundError(error_msg)
        
        try:
            # Read CSV with specific columns by index
            # CSV structure (Excel-exported format):
            #  0: Date
            #  1: Time
            #  2: Product
            #  3: ISIN
            #  4: Reference (Exchange)
            #  5: Venue (skipped)
            #  6: Quantity
            #  7: Price
            #  8: Price_Currency (EUR, skipped)
            #  9: Local_Value
            # 10: Local_Value_Currency (EUR, skipped)
            # 11: Value
            # 12: Value_Currency (EUR, skipped)
            # 13: Exchange_Rate
            # 14: Transaction_Costs
            # 15: Transaction_Costs_Currency (EUR, skipped)
            # 16: Total
            # 17: Total_Currency (EUR, skipped)
            # 18: Order_ID (skipped)
            
            usecols = [0, 1, 2, 3, 4, 6, 7, 9, 11, 13, 14, 16]
            column_names = [
                'Date', 'Time', 'Product_Name_DeGiro', 'ISIN', 'Exchange',
                'Quantity', 'Price', 'Local_Value', 'Value', 'Exchange_Rate',
                'Transaction_Costs', 'Total'
            ]
            
            df = pd.read_csv(self.csv_path, usecols=usecols, header=0, sep=",")
            df.columns = column_names
            
            return df
        
        except Exception as e:
            error_msg = f"Error loading CSV: {e}"
            app_logger.error(f"[TRANSACTIONS] {error_msg}", exc_info=True)
            raise
    
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

        # Load existing mapping from file
        existing_mapping = self._load_existing_mapping()

        # Ensure FULL_PORTFOLIO entry exists
        if "FULL_PORTFOLIO" not in existing_mapping.keys():
            existing_mapping["FULL_PORTFOLIO"] = {
                "ticker": "FULL",
                "degiro_name": "Full portfolio",
                "display_name": "Full portfolio",
                "exchange": "",
                "product_type": ""
            }

        # Get unique ISINs with validation
        valid_isins_df = self._get_valid_isins(df)

        if valid_isins_df.empty:
            app_logger.info("[ISIN-MAPPING] No valid ISINs to process")
            return existing_mapping

        # Process new ISINs
        new_isins_count = self._process_new_isins(valid_isins_df, existing_mapping)

        # Save only if there were changes
        if new_isins_count > 0:
            self._save_mapping_file(existing_mapping)
            app_logger.info(f"[ISIN-MAPPING] Added {new_isins_count} new ISIN mappings")

        return existing_mapping

    def _load_existing_mapping(self) -> Dict:
        """Load existing ISIN mapping."""
        try:
            if self.mapping_path.exists():
                with open(self.mapping_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
            app_logger.warning(f"[ISIN-MAPPING] Error loading existing mapping: {e}")
        return {}

    def _get_valid_isins(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and validate unique ISINs from DataFrame."""
        valid_isins_df = df[['ISIN', 'Product_Name_DeGiro', 'Exchange']].drop_duplicates()

        # Filter valid ISINs: not null, not empty after stripping whitespace
        valid_mask = (
            valid_isins_df['ISIN'].notna() &
            (valid_isins_df['ISIN'].astype(str).str.strip() != "")
        )
        return valid_isins_df[valid_mask]

    def _process_new_isins(self, valid_isins_df: pd.DataFrame, existing_mapping: Dict) -> int:
        """Process new ISINs and add them to mapping. Returns count of new ISINs added."""
        existing_isins = set(existing_mapping.keys())
        new_isins_count = 0

        for isin, name, exchange in valid_isins_df.values:
            if isin not in existing_isins:
                try:
                    product = self._get_yahoo_product(
                        isin=isin,
                        exchange=self.degiro_to_yf_exchange.get(exchange)
                    )
                except Exception as e:
                    app_logger.warning(f"[ISIN-MAPPING] Failed to get product info for {isin}: {e}")
                    product = {}

                app_logger.info(f"[ISIN-MAPPING] Adding {isin} -> {name}")
                existing_mapping[isin] = {
                    "ticker": product.get("symbol", ""),
                    "degiro_name": name,
                    "display_name": product.get("shortname", name),
                    "exchange": str(exchange),
                    "product_type": product.get("quoteType", "")
                }
                new_isins_count += 1

        return new_isins_count

    def _save_mapping_file(self, mapping: Dict) -> None:
        """Save mapping to file with proper error handling."""
        try:
            self.mapping_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.mapping_path, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, indent=4, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"[ISIN-MAPPING] Failed to save mapping file: {e}")
            raise
    
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
            app_logger.info("[TRANSACTIONS] Starting data preparation...")
            
            # Parse dates and times first
            df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
            df['Time'] = pd.to_datetime(df['Time'], format='%H:%M').dt.time

            # Ensure correct types
            df['Quantity'] = df['Quantity'].fillna(0).astype(int)
            df['Exchange'] = df['Exchange'].fillna('').astype(str)
            
            # Determine action (BUY/SELL)
            df['Action'] = df['Quantity'].apply(lambda x: 'BUY' if x > 0 else 'SELL')
            
            # Convert numeric columns (handle both dot and comma decimal separators)
            float_columns = ['Price', 'Local_Value', 'Value', 'Exchange_Rate', 'Transaction_Costs', 'Total']
            for col in float_columns:
                df[col] = (
                    df[col]
                    .fillna("0")
                    .astype(str)
                    .str.replace(",", ".")  # Handle comma as decimal separator
                    .astype(float)
                )
            
            # Sort chronologically
            df = df.sort_values(by=["Date", "Time"]).reset_index(drop=True)
            
            app_logger.info(f"[TRANSACTIONS] Data preparation completed successfully with {len(df)} rows")
            return df
            
        except Exception as e:
            app_logger.error(f"[TRANSACTIONS] Error preparing data: {e}", exc_info=True)
            return pd.DataFrame()


# Singleton instance
transaction_service = TransactionService()


# Convenience function for backward compatibility
# TODO : Remove in future refactor
def get_transactions() -> pd.DataFrame:
    """Get all transactions (backward compatible with old code)."""
    return transaction_service.get_all_transactions()
