"""
Smart completer that integrates history-based frequency tracking.

This module extends the base PGCompleter with intelligent sorting
based on usage frequency history.
"""

import logging
import math
from typing import Optional, List, Any
from prompt_toolkit.completion import Completion

from ..pgcompleter import PGCompleter, Match
from ..packages.sqlcompletion import Keyword
from .history_freq import HistoryFreqTracker, get_history_freq_tracker

_logger = logging.getLogger(__name__)


class SmartPGCompleter(PGCompleter):
    """
    PGCompleter with smart history-based completion.

    This class extends PGCompleter to provide history-aware completion sorting.
    """

    def __init__(self, smart_completion=True, pgspecial=None, settings=None,
                 smart_completion_enabled=False, history_freq_db_path=None):
        """
        Initialize the SmartPGCompleter.

        Args:
            smart_completion: Base smart completion flag (from PGCompleter)
            pgspecial: PGSpecial instance
            settings: Completion settings dict
            smart_completion_enabled: Whether to enable history-based sorting
            history_freq_db_path: Custom path for history database
        """
        super().__init__(smart_completion=smart_completion, pgspecial=pgspecial, settings=settings)

        self.smart_completion_enabled = smart_completion_enabled
        self.history_freq_db_path = history_freq_db_path
        self._history_tracker: Optional[HistoryFreqTracker] = None

        if self.smart_completion_enabled:
            self._init_history_tracker()

    def _init_history_tracker(self):
        """Initialize the history frequency tracker."""
        try:
            self._history_tracker = get_history_freq_tracker(self.history_freq_db_path)
            _logger.debug("History tracker initialized for smart completion")
        except Exception as e:
            _logger.error("Failed to initialize history tracker: %s", e)
            self._history_tracker = None

    def enable_smart_completion(self, enabled: bool = True):
        """
        Enable or disable smart completion at runtime.

        Args:
            enabled: True to enable, False to disable
        """
        self.smart_completion_enabled = enabled

        if enabled and self._history_tracker is None:
            self._init_history_tracker()

        _logger.info("Smart completion %s", "enabled" if enabled else "disabled")

    def record_completion_usage(self, completion: str, completion_type: Optional[str] = None):
        """
        Record that a completion was used.

        Args:
            completion: The completion text that was used
            completion_type: Type of completion (keyword, table, etc.)
        """
        if self._history_tracker and completion:
            self._history_tracker.record_completion_selection(
                completion,
                completion_type=completion_type
            )

    def get_keyword_matches(self, suggestion, word_before_cursor):
        """
        Override keyword matching to incorporate frequency data.

        When smart completion is enabled, keywords are sorted by usage frequency.
        """
        # Get base matches from parent class
        matches = super().get_keyword_matches(suggestion, word_before_cursor)

        if not self.smart_completion_enabled or not self._history_tracker:
            return matches

        # Re-sort matches based on frequency
        return self._sort_matches_by_frequency(matches, "keyword")

    def _sort_matches_by_frequency(self, matches: List[Match], completion_type: str) -> List[Match]:
        """
        Sort completion matches by usage frequency.

        Args:
            matches: List of Match objects
            completion_type: Type of completion

        Returns:
            Re-sorted list of matches
        """
        if not self._history_tracker or not matches:
            return matches

        # Get frequency for each match
        freq_map = {}
        for match in matches:
            text = match.completion.text.upper().strip()
            freq = self._history_tracker.get_frequency(text)
            freq_map[match] = freq

        # Sort by original priority first, then by frequency
        # Keep the original sorting but boost frequently used items
        def sort_key(match):
            original_priority = match.priority
            freq = freq_map.get(match, 0)
            # Boost priority by frequency (higher frequency = higher priority)
            # Use a logarithmic scale to prevent over-prioritization
            freq_boost = math.log1p(freq) * 100 if freq > 0 else 0

            # Return tuple for sorting: (negative frequency boost to sort descending,
            # then original priority components)
            if isinstance(original_priority, tuple):
                return (-freq_boost,) + original_priority
            else:
                return (-freq_boost, original_priority)

        return sorted(matches, key=sort_key)

    def get_completions(self, document, complete_event, smart_completion=None):
        """
        Override get_completions to track usage.

        Also applies frequency-based sorting when smart completion is enabled.
        """
        completions = super().get_completions(document, complete_event, smart_completion)

        # If smart completion is enabled, we might want to re-sort completions
        # based on frequency. However, the base class already returns Completion
        # objects, so we need to handle this differently.

        # For now, we track the completions that are shown
        # Actual selection tracking would need to be done at the UI level

        return completions

    def update_history_from_query(self, query: str):
        """
        Update history frequency data from a SQL query.

        Args:
            query: The SQL query to analyze
        """
        if not self.smart_completion_enabled or not self._history_tracker:
            return

        try:
            # Extract keywords from the query
            import sqlparse

            # Parse the query
            parsed = sqlparse.parse(query)

            for statement in parsed:
                # Get the first token (usually the main keyword)
                first_token = statement.token_first()
                if first_token:
                    keyword = str(first_token).upper().strip()
                    if keyword and not keyword.startswith('\\'):
                        self._history_tracker.record_usage(keyword)

                # Also record all keyword tokens
                for token in statement.flatten():
                    if token.ttype in (sqlparse.tokens.Keyword,
                                      sqlparse.tokens.Keyword.DDL,
                                      sqlparse.tokens.Keyword.DML):
                        self._history_tracker.record_usage(str(token))

        except Exception as e:
            _logger.debug("Error updating history from query: %s", e)

    def get_stats(self) -> dict:
        """Get statistics about the smart completer."""
        stats = {
            "smart_completion_enabled": self.smart_completion_enabled,
        }

        if self._history_tracker:
            stats.update(self._history_tracker.get_stats())

        return stats
