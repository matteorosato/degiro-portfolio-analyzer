"""
Formatting utilities for display values.

Provides functions to format numbers, currencies, and UI elements.
"""

from typing import Tuple
from src.utils.styling import get_badge_color, get_badge_icon


def format_portfolio_badge(
    current_value: float,
    daily_delta: float,
    daily_delta_per: float
) -> Tuple[str, str, str]:
    """
    Format portfolio value badge with color, icon, and text.
    
    Args:
        current_value: Current portfolio value
        daily_delta: Daily change in euros
        daily_delta_per: Daily change in percentage
    
    Returns:
        Tuple of (color, icon, text) for badge display
    """
    color = get_badge_color(daily_delta)
    icon = get_badge_icon(daily_delta)
    
    # Format the text based on delta value
    if daily_delta > 0:
        text = (
            f"Portfolio Value: € {abs(current_value):,.2f} "
            f"(∆ +{daily_delta_per}% | +€ {abs(daily_delta)})"
        )
    elif daily_delta < 0:
        text = (
            f"Portfolio Value: € {abs(current_value):,.2f} "
            f"(∆ {daily_delta_per}% | -€ {abs(daily_delta)})"
        )
    else:
        text = f"Portfolio Value: € {abs(current_value):,.2f}"
    
    return color, icon, text
