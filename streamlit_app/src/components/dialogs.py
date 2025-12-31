"""Dialog components for user interactions.

This module provides reusable dialog components for common user interactions.
"""

from typing import Callable, Optional
import streamlit as st
from src.api.client import upload_transactions_file, delete_all_data
from src.utils.error_handler import handle_api_error


def show_confirm_upload_dialog(
    uploaded_file,
    on_success_callback: Optional[Callable] = None
) -> None:
    """Show confirmation dialog for file upload.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        on_success_callback: Optional callback to run on successful upload
    """
    @st.dialog("Confirm Upload")
    def _dialog():
        st.warning("Replace Transactions File?")
        st.markdown(
            "Uploading a new transactions file will replace the existing one and "
            "recalculate your entire portfolio. This action cannot be undone."
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("OK", use_container_width=True, type="primary"):
                st.session_state.processing = True
                st.rerun()

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.pending_file_upload = None
                st.session_state.upload_count += 1
                st.rerun()

        if st.session_state.get("processing"):
            with st.spinner("Processing and recalculating portfolio..."):
                result = upload_transactions_file(uploaded_file)

            if result and result.get("status") == "success":
                st.success(f"✅ {result['message']}")
                st.session_state.processing = False
                st.session_state.pending_file_upload = None
                st.session_state.startup_refresh = False
                st.session_state.upload_count += 1
                
                if on_success_callback:
                    on_success_callback(result)
                
                st.rerun()
            else:
                st.error("Failed to upload file")
                st.session_state.processing = False
    
    _dialog()


def show_reset_dialog(on_success_callback: Optional[Callable] = None) -> None:
    """Show confirmation dialog for resetting all data.
    
    Args:
        on_success_callback: Optional callback to run on successful reset
    """
    @st.dialog("Reset Everything")
    def _dialog():
        st.warning("**WARNING: This will delete all portfolio data!**")
        st.markdown("This action **cannot be undone**. Cached calculations will be removed.")

        if st.button("Yes, Reset All", use_container_width=True, type="primary"):
            with st.spinner("Resetting..."):
                try:
                    delete_all_data()
                    st.success("Reset complete!")
                    
                    if on_success_callback:
                        on_success_callback()
                    
                except Exception as e:
                    handle_api_error(e, "Reset failed", stop=False)

            st.session_state.startup_refresh = False
            st.rerun()

        if st.button("Cancel", use_container_width=True):
            st.rerun()
    
    _dialog()
