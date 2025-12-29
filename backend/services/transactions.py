"""Compatibility wrapper for old transactions service imports.

This module redirects to the new transactions service location
to maintain backward compatibility with existing code.
"""
from backend.app.routers.transactions.services import transaction_service


def get_transactions():
    """Get all transactions - compatibility wrapper."""
    return transaction_service.get_all_transactions()
