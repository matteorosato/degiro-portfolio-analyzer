"""Compatibility wrapper for old logger imports.

This module redirects to the new logger location in backend.app.shared.logger
to maintain backward compatibility with existing code.
"""
from backend.app.shared.logger import app_logger, scheduler_logger

__all__ = ["app_logger", "scheduler_logger"]
