"""
Smart SQL completion module with history-based frequency tracking.

This module provides intelligent SQL keyword completion by tracking
usage frequency and prioritizing frequently used keywords.
"""

from .history_freq import HistoryFreqTracker, get_history_freq_tracker
from .smart_completer import SmartPGCompleter
from ..pgcompleter import PGCompleter


def create_completer(smart_completion=True, pgspecial=None, settings=None, smart_completion_history=False):
    """
    Factory function to create the appropriate completer based on configuration.

    Args:
        smart_completion: Base smart completion flag
        pgspecial: PGSpecial instance
        settings: Completion settings dict
        smart_completion_history: Whether to enable history-based smart completion

    Returns:
        PGCompleter or SmartPGCompleter instance
    """
    if smart_completion_history:
        return SmartPGCompleter(
            smart_completion=smart_completion,
            pgspecial=pgspecial,
            settings=settings,
            smart_completion_enabled=True
        )
    else:
        return PGCompleter(
            smart_completion=smart_completion,
            pgspecial=pgspecial,
            settings=settings
        )


__all__ = ["HistoryFreqTracker", "get_history_freq_tracker", "SmartPGCompleter", "create_completer"]
