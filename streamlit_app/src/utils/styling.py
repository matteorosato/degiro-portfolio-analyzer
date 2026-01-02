"""
Styling utilities for Streamlit components.

Provides reusable styling functions for consistent UI appearance.
"""

from config import ColorScheme


def color_net_performance(val: float) -> str:
    """
    Return CSS color string based on performance value.
    
    Args:
        val: Performance value (positive, negative, or zero)
    
    Returns:
        CSS color string formatted as 'color: {color}'
    """
    if val > 0:
        color = ColorScheme.POSITIVE
    elif val < 0:
        color = ColorScheme.NEGATIVE
    else:
        color = ColorScheme.NEUTRAL
    
    return f'color: {color}'


def get_badge_color(value: float) -> str:
    """
    Get badge color based on value.
    
    Args:
        value: Numeric value to evaluate
    
    Returns:
        Color name for badge ('green', 'red', or 'gray')
    """
    if value > 0:
        return 'green'
    elif value < 0:
        return 'red'
    else:
        return 'gray'


def get_badge_icon(value: float) -> str:
    """
    Get badge icon based on value.
    
    Args:
        value: Numeric value to evaluate
    
    Returns:
        Material icon string
    """
    if value > 0:
        return ':material/arrow_upward:'
    elif value < 0:
        return ':material/arrow_downward:'
    else:
        return ':material/info:'
