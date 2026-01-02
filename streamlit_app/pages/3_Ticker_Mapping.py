import json
import time

import pandas as pd
import streamlit as st

from src.api.client import fetch_isin_mapping, save_isin_mapping
from src.data.transformers import prepare_mapping_dataframe
from src.services.ticker_service import (
    search_ticker,
    build_mapping_dict,
    load_mapping_dict,
)
from src.utils.error_handler import handle_api_error

# ============================================================================
# MAPPING CONSTANTS
# ============================================================================

DISABLED_MAPPING_COLUMNS = ["ISIN", "Exchange", "Product Name (DeGiro)"]

# Set the page title
st.set_page_config(page_title="Ticker Mapping", page_icon="📊", layout="wide")

# Load ISIN mapping via API
try:
    mapping = fetch_isin_mapping()
except Exception as e:
    handle_api_error(e, "Mapping not found. Make sure to upload and process transactions first",
                     show_exception=True)

# Load or initialize mapping
if 'mapping_df' not in st.session_state:
    st.session_state.mapping_df = prepare_mapping_dataframe(mapping)
    st.session_state.refresh_mapping = False


def save_mapping(df):
    """Save mapping to backend."""
    updated_mapping = build_mapping_dict(df)

    # Save to backend
    try:
        response = save_isin_mapping(updated_mapping)
        if response.get("success"):
            # Signal cache refresh on next page load
            st.session_state.refresh_mapping = True
            st.cache_data.clear()
            st.toast(f"✅ Mapping saved!")
        else:
            st.error("Failed to save mapping")
    except Exception as e:
        st.error(f"Error saving mapping: {str(e)}")


# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title("Ticker Mapping")

st.info(
    "**Quick help:**\n\n"
    "**🔄 Auto-fill empty tickers** - Search Yahoo Finance to automatically fill missing ticker symbols\n\n"
    "**💾 Save Mapping** - Save all the current changes (required to apply modifications)\n\n"
    "**⚙️ Advanced Options** - Import/export mapping as JSON or reset all tickers"
)

# ============================================================================
# TOOLBAR
# ============================================================================

# Custom CSS for smaller buttons
st.markdown("""
    <style>
    div[data-testid="stButton"] > button {
        padding-top: 0.25rem;
        padding-bottom: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Auto-fill empty tickers", use_container_width=True):
        new_df = st.session_state.mapping_df.copy()
        total_empty = (new_df["Ticker"] == "").sum()

        if total_empty == 0:
            st.info("No empty tickers to fill!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            filled_count = 0

            for idx, (i, row) in enumerate(new_df[new_df["Ticker"] == ""].iterrows()):
                display_name = row["Display Name"] if row["Display Name"] else row["Product Name (DeGiro)"]
                exch = row["Exchange"] if row["Exchange"] else None
                status_text.text(f"Searching: {display_name[:30]}...")
                guessed_ticker = search_ticker(display_name, exch)
                if guessed_ticker:
                    new_df.at[i, "Ticker"] = guessed_ticker[0]
                    filled_count += 1
                progress_bar.progress((idx + 1) / total_empty)
                time.sleep(1)

            st.session_state.mapping_df = new_df
            save_mapping(new_df)
            status_text.empty()
            progress_bar.empty()
            st.success(f"Filled {filled_count}/{total_empty} tickers!")
            time.sleep(1.5)
            st.rerun()

with col2:
    if st.button("💾 Save Mapping", type="primary", use_container_width=True):
        save_mapping(st.session_state.mapping_df)

with col3:
    with st.popover("⚙️ Advanced Options", use_container_width=True):
        st.subheader("Options")

        # Import Section
        st.markdown("**Import Mapping**")

        uploaded_mapping = st.file_uploader("Upload JSON", type=["json"], label_visibility="collapsed")

        if uploaded_mapping:
            try:
                new_mapping = json.load(uploaded_mapping)
                if not isinstance(new_mapping, dict):
                    st.error("Invalid JSON format.")
                else:
                    st.session_state.mapping_df = load_mapping_dict(new_mapping)
                    st.success("Mapping loaded!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        st.divider()

        # Export Section
        st.markdown("**Export Mapping**")

        # Download current mapping
        current_mapping = build_mapping_dict(st.session_state.mapping_df)
        json_bytes = json.dumps(current_mapping, indent=4).encode('utf-8')

        st.download_button(
            label="📥 Download JSON",
            data=json_bytes,
            file_name="isin_mapping.json",
            mime="application/json",
            use_container_width=True
        )

        st.divider()

        # Reset Section
        st.markdown("**⚠️ Danger Zone**")
        st.caption("This will clear all tickers and reset display names.")

        if st.button("Reset All Tickers", type="secondary", use_container_width=True):
            reset_df = st.session_state.mapping_df.copy()
            reset_df["Ticker"] = ""
            reset_df["Display Name"] = reset_df["Product Name (DeGiro)"]
            st.session_state.mapping_df = reset_df
            save_mapping(reset_df)
            st.success("Reset complete!")
            time.sleep(1)
            st.rerun()

st.divider()

# ============================================================================
# EDITABLE TABLE
# ============================================================================

# Filter out FULL from table display (but keep in session for save)
table_df = st.session_state.mapping_df[st.session_state.mapping_df["Ticker"] != "FULL"]

# Display editable DataFrame
edited_df = st.data_editor(
    table_df.sort_values(by=["Product Name (DeGiro)"], ascending=True),
    column_config={
        "Product Type": st.column_config.TextColumn(
            "Type",
            help="Type of product (Stock, ETF, Bond, etc.)",
            width="medium",
        )
    },
    disabled=DISABLED_MAPPING_COLUMNS,
    hide_index=True,
    num_rows="fixed",
    key="editable_table"
)

# Update session state with edited data
st.session_state.mapping_df = edited_df
