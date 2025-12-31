"""Error handling utilities.

This module provides standardized error handling for the application.
"""

import streamlit as st
from typing import Optional


def handle_api_error(
    error: Exception,
    message: str,
    stop: bool = True,
    show_exception: bool = False
) -> None:
    """Handle API errors with consistent messaging.
    
    Args:
        error: The exception that occurred
        message: User-friendly error message
        stop: Whether to stop execution after showing error
        show_exception: Whether to show full exception details
    """
    st.error(f"{message}: {error}")
    
    if show_exception:
        st.exception(error)
    
    if stop:
        st.stop()


def show_warning(message: str) -> None:
    """Display a warning message.
    
    Args:
        message: Warning message to display
    """
    st.warning(message)


def show_success(message: str) -> None:
    """Display a success message.
    
    Args:
        message: Success message to display
    """
    st.success(message)


def show_info(message: str) -> None:
    """Display an info message.
    
    Args:
        message: Info message to display
    """
    st.info(message)
