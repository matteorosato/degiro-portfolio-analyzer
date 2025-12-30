#!/usr/bin/env python3
"""
Test script for transaction services optimization.
"""
import sys
import os
import pandas as pd

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.routers.transactions.services import TransactionService

def test_csv_loading():
    """Test CSV loading with optimized code."""
    print("Testing CSV loading...")

    # Initialize service
    service = TransactionService()

    try:
        # Load data
        df = service._load_data()
        print(f"Loaded {len(df)} rows")
        print(f"Columns: {list(df.columns)}")

        # Check data types
        print("\nData types:")
        print(df.dtypes)

        # Check sample data
        print("\nSample data:")
        print(df.head(3))

        # Test ISIN mapping
        print("\nTesting ISIN mapping...")
        mapped_df = service._map_isin(df)
        print(f"Mapped columns: {list(mapped_df.columns)}")
        print("Sample mapped data:")
        print(mapped_df[['ISIN', 'Stock', 'Product']].head(3))

        # Test data preparation
        print("\nTesting data preparation...")
        try:
            prepared_df = service._prepare_data(mapped_df)
            print(f"Prepared DataFrame shape: {prepared_df.shape}")
            print(f"Prepared columns: {list(prepared_df.columns)}")
            if not prepared_df.empty:
                print("Sample prepared data:")
                print(prepared_df[['Date', 'Quantity', 'Price', 'Action']].head(3))
            else:
                print("❌ Prepared DataFrame is empty!")
        except Exception as e:
            print(f"❌ Exception in _prepare_data: {e}")
            import traceback
            traceback.print_exc()

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_csv_loading()