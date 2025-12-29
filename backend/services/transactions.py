import pandas as pd
import os
import json
import warnings
import yfinance as yf
from backend.utils.logger import app_logger
from backend.config import FilePaths

warnings.simplefilter(action='ignore', category=pd.errors.SettingWithCopyWarning)

# File Paths
TRANSACTION_FILE = FilePaths.TRANSACTION_CSV
MAPPING_FILE = FilePaths.ISIN_MAPPING


def get_yahoo_product(isin: str, exchange: str = None) -> dict:
    """
    Retrieves product information from Yahoo Finance using an ISIN code.

    The function works as follows:
    1. Uses the ISIN to search for the product and retrieve its full name ('longname')
    2. Performs a second search using the product's longname to find all matching products across exchanges
    3. If a desired exchange is provided, attempts to find and return the product from that specific exchange
    4. Returns an empty dictionary if no results are found at any step or if no exchange is provided

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

    # Search for the product with the desired exchange
    for quote in results_by_product_name.quotes:
        if quote.get('exchange') == exchange:
            return quote

    return {}



def update_isin_mapping_json(df: pd.DataFrame):
    """
    Reads the transactions df, finds new ISINs, and updates the mapping JSON file.
    """
    # Ensure required columns for mapping exist
    required_cols = {'ISIN', 'Product_Name_DeGiro', 'Exchange'}
    if not required_cols.issubset(df.columns):
        app_logger.warning("[ISIN-MAPPING] Columns required for ISIN mapping are missing. Skipping update.")
        return None

    # Load existing mapping or initialize an empty one
    try:
        with open(MAPPING_FILE, 'r') as f:
            existing_mapping = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_mapping = {}
    
    # Find unique ISINs from the transaction data
    isin_list = df[['ISIN', 'Product_Name_DeGiro', 'Exchange']].drop_duplicates()
    isin_list = isin_list[isin_list['ISIN'].notna() & (isin_list['ISIN'].astype(str).str.strip() != "")]

    # Exchange mapping from Degiro to Yahoo Finance
    # TODO move this to constants
    degiro_2_yf_mapping = {
        "EAM": "AMS",
        "XET": "GER",
        "MIL": "MIL",
        "LSE": "LSE",
        "NDQ": "NYQ",
        "NSY": "SWX",
        # "TDG": "XET",
        # "EPA": "PAR",
    }

    # Add new ISINs to the mapping without overwriting existing entries
    for isin, name, exchange in isin_list.values:
        try:
            product = get_yahoo_product(isin=isin, exchange=degiro_2_yf_mapping.get(exchange))
        except Exception as e:
            product = {}
        if isin not in existing_mapping:
            app_logger.info(f"[ISIN-MAPPING] Adding new ISIN mapping: {isin} -> {name}")
            existing_mapping[isin] = {
                "ticker": product.get("symbol", ""),
                "degiro_name": name,
                "display_name": product.get("shortname", name),
                "exchange": exchange,
                "product_type": product.get("quoteType", "")
            }
    
    # Ensure the special "FULL_PORTFOLIO" entry exists
    if "FULL_PORTFOLIO" not in existing_mapping:
         existing_mapping["FULL_PORTFOLIO"] = {
            "ticker": "FULL", "degiro_name": "Full portfolio", 
            "display_name": "Full portfolio", "exchange": "", "product_type": ""
         }

    # Save the updated mapping back to the JSON file
    with open(MAPPING_FILE, 'w') as f:
        json.dump(existing_mapping, f, indent=4)
    
    return existing_mapping


def load_data() -> pd.DataFrame:
    """
    Loads transactions from CSV and performs basic column mapping.

    Returns:
        pd.DataFrame: Raw transaction data with standardized column names
    """
    if not os.path.exists(TRANSACTION_FILE):
        app_logger.warning(f"[TRANSACTIONS] Transaction file not found at {TRANSACTION_FILE}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(TRANSACTION_FILE)

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

        # Apply mapping safely
        column_indices = list(column_names.keys())
        df = df.iloc[:, column_indices]
        df.columns = list(column_names.values())

        # TODO remove when done. This is needed for the mapping
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
        app_logger.error(f"[TRANSACTIONS] Error loading transaction data: {e}", exc_info=True)
        return pd.DataFrame()


def map_isin(df: pd.DataFrame) -> pd.DataFrame:
    """
    Updates ISIN mapping file and applies ticker mapping to the DataFrame.

    Args:
        df: Raw transaction DataFrame from load_data()

    Returns:
        pd.DataFrame: DataFrame with Stock and Product columns added from mapping
    """
    if df.empty:
        return df

    try:
        # Update the ISIN mapping file based on the raw transactions
        app_logger.info("[ISIN-MAPPING] Updating ISIN mapping from transaction data...")
        isin_mapping = update_isin_mapping_json(df)
        app_logger.info("[ISIN-MAPPING] ISIN mapping updated successfully.")

        # Apply the mapping to the DataFrame
        if isin_mapping:
            df['Stock'] = df['ISIN'].apply(lambda isin: isin_mapping.get(isin, {}).get("ticker", "")).astype(str)
            df['Product'] = df['ISIN'].apply(lambda isin: isin_mapping.get(isin, {}).get("display_name", "")).astype(str)
        else:
            df['Stock'] = ''
            df['Product'] = ''

        return df

    except Exception as e:
        app_logger.error(f"[ISIN-MAPPING] Error during ISIN mapping: {e}", exc_info=True)
        # Add empty Stock and Product columns if mapping fails
        df['Stock'] = ''
        df['Product'] = ''
        return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and transforms transaction data.
    Assumes Stock and Product columns are already present from map_isin().

    Args:
        df: Transaction DataFrame from map_isin()

    Returns:
        pd.DataFrame: Cleaned and processed transaction data
    """
    if df.empty:
        return df

    try:
        # Data cleaning and transformation
        df['Action'] = df['Quantity'].apply(lambda x: 'BUY' if x > 0 else 'SELL')
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
        df['Time'] = pd.to_datetime(df['Time'], format='%H:%M').dt.time

        # Convert numeric columns with comma as decimal separator
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
        # TODO fix this name
        df['Cost'] = (
            df['Value']
            .fillna("0")
            .astype(str)
            .str.replace(",", ".")
            .astype(float)
        )
        # TODO fix this name
        df['Transaction_costs'] = (
            df['Transaction_Costs']
            .fillna("0")
            .astype(str)
            .str.replace(",", ".")
            .astype(float)
        )

        # df = df.dropna()
        # Sort transactions chronologically and return
        return df.sort_values(by=["Date", "Time"]).reset_index(drop=True)

    except Exception as e:
        app_logger.error(f"[TRANSACTIONS] Error preparing transaction data: {e}", exc_info=True)
        return pd.DataFrame()


def get_transactions() -> pd.DataFrame:
    """
    Returns a copy of the cleaned transactions DataFrame.
    Workflow: load_data() → map_isin() → prepare_data()

    Ensures consumers can't modify the original data.
    """
    try:
        app_logger.info("[TRANSACTIONS] Processing transactions...")

        # Step 1: Load raw data from CSV and standardize columns
        raw_df = load_data()

        # Step 2: Update ISIN mapping and apply Stock/Product mapping
        mapped_df = map_isin(raw_df)

        # Step 3: Clean and transform the data
        transactions_df = prepare_data(mapped_df)

        app_logger.info("[TRANSACTIONS] Transactions processed successfully.")

    except Exception as e:
        app_logger.error(f"[TRANSACTIONS] Error during transactions processing: {e}", exc_info=True)
        raise e
    
    return transactions_df.copy()