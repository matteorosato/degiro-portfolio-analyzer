"""Session state management utilities.

This module provides helpers for managing Streamlit session state.
"""

from typing import Dict, Any
import streamlit as st


def initialize_session_state(defaults: Dict[str, Any]) -> None:
    """Initialize session state variables with default values.
    
    Args:
        defaults: Dictionary of {key: default_value} to initialize
    """
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session_value(key: str, default: Any = None) -> Any:
    """Get a value from session state with a default fallback.
    
    Args:
        key: Session state key
        default: Default value if key doesn't exist
        
    Returns:
        Value from session state or default
    """
    return st.session_state.get(key, default)


def set_session_value(key: str, value: Any) -> None:
    """Set a value in session state.
    
    Args:
        key: Session state key
        value: Value to set
    """
    st.session_state[key] = value
