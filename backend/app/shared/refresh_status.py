"""Refresh status manager for portfolio background tasks."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


RefreshStatus = Literal["idle", "running", "completed", "failed"]


class RefreshState(BaseModel):
    """State of portfolio refresh operation."""
    
    status: RefreshStatus = "idle"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    model_config = {"frozen": False}


# Global state instance
_refresh_state = RefreshState()


def get_refresh_status() -> RefreshState:
    """Get current refresh status."""
    return _refresh_state


def set_refresh_running() -> None:
    """Mark refresh as running."""
    global _refresh_state
    _refresh_state.status = "running"
    _refresh_state.started_at = datetime.now()
    _refresh_state.completed_at = None
    _refresh_state.error_message = None


def set_refresh_completed() -> None:
    """Mark refresh as completed."""
    global _refresh_state
    _refresh_state.status = "completed"
    _refresh_state.completed_at = datetime.now()


def set_refresh_failed(error: str) -> None:
    """Mark refresh as failed."""
    global _refresh_state
    _refresh_state.status = "failed"
    _refresh_state.completed_at = datetime.now()
    _refresh_state.error_message = error


def set_refresh_idle() -> None:
    """Reset to idle state."""
    global _refresh_state
    _refresh_state = RefreshState()


def is_refresh_running() -> bool:
    """Check if refresh is currently running."""
    return _refresh_state.status == "running"
