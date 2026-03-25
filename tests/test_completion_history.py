"""
Tests for the smart completion history frequency tracking feature.
"""

import os
import tempfile
import pytest
from pgcli.completion.history_freq import HistoryFreqTracker


class TestHistoryFreqTracker:
    """Tests for HistoryFreqTracker class."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.tracker = HistoryFreqTracker(self.temp_db.name)

    def teardown_method(self):
        """Cleanup after each test method."""
        self.tracker.close()
        # Create a new instance to avoid singleton issues
        HistoryFreqTracker._instance = None
        HistoryFreqTracker._initialized = False
        if os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                pass  # File may still be locked

    def test_record_and_get_frequency(self):
        """Test recording and retrieving keyword frequency."""
        # Record some usage
        self.tracker.record_usage("SELECT", 5)
        self.tracker.record_usage("FROM", 3)
        self.tracker.record_usage("WHERE", 1)

        # Check frequencies
        assert self.tracker.get_frequency("SELECT") == 5
        assert self.tracker.get_frequency("FROM") == 3
        assert self.tracker.get_frequency("WHERE") == 1
        assert self.tracker.get_frequency("JOIN") == 0  # Not recorded

    def test_record_increment(self):
        """Test that recording increments existing counts."""
        self.tracker.record_usage("SELECT", 5)
        self.tracker.record_usage("SELECT", 3)

        assert self.tracker.get_frequency("SELECT") == 8

    def test_case_insensitive(self):
        """Test that keywords are stored case-insensitively."""
        self.tracker.record_usage("select", 5)
        self.tracker.record_usage("SELECT", 3)
        self.tracker.record_usage("Select", 2)

        assert self.tracker.get_frequency("select") == 10
        assert self.tracker.get_frequency("SELECT") == 10
        assert self.tracker.get_frequency("SELECT") == 10

    def test_get_all_frequencies(self):
        """Test getting all frequencies."""
        self.tracker.record_usage("SELECT", 5)
        self.tracker.record_usage("FROM", 3)

        freqs = self.tracker.get_all_frequencies()

        assert freqs["SELECT"] == 5
        assert freqs["FROM"] == 3

    def test_get_top_keywords(self):
        """Test getting top keywords."""
        self.tracker.record_usage("SELECT", 10)
        self.tracker.record_usage("FROM", 5)
        self.tracker.record_usage("WHERE", 8)
        self.tracker.record_usage("JOIN", 3)

        top = self.tracker.get_top_keywords(limit=2)

        assert len(top) == 2
        assert top[0] == ("SELECT", 10)
        assert top[1] == ("WHERE", 8)

    def test_record_completion_selection(self):
        """Test recording completion selection."""
        self.tracker.record_completion_selection("users", "table", "SELECT")
        self.tracker.record_completion_selection("id", "column", "SELECT")

        # Should also update keyword frequency
        assert self.tracker.get_frequency("USERS") >= 1
        assert self.tracker.get_frequency("ID") >= 1

    def test_clear_history(self):
        """Test clearing history."""
        self.tracker.record_usage("SELECT", 5)
        self.tracker.clear_history()

        assert self.tracker.get_frequency("SELECT") == 0
        assert self.tracker.get_stats()["unique_keywords"] == 0

    def test_get_stats(self):
        """Test getting statistics."""
        self.tracker.record_usage("SELECT", 5)
        self.tracker.record_usage("FROM", 3)

        stats = self.tracker.get_stats()

        assert stats["unique_keywords"] == 2
        assert stats["total_usage"] == 8

        # Test with completion selection (which also records keyword)
        self.tracker.record_completion_selection("users", "table")
        stats = self.tracker.get_stats()
        assert stats["total_completions"] == 1
        # Now we have 3 keywords: SELECT, FROM, and USERS (from completion_selection)

    def test_empty_keyword_handling(self):
        """Test handling of empty keywords."""
        # Should not raise
        self.tracker.record_usage("")
        self.tracker.record_usage(None)
        self.tracker.record_completion_selection("")

        assert self.tracker.get_frequency("") == 0


class TestSmartCompleterIntegration:
    """Tests for SmartPGCompleter integration with history tracking."""

    def setup_method(self):
        """Setup for each test method."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()

    def teardown_method(self):
        """Cleanup after each test method."""
        # Reset singleton
        from pgcli.completion.history_freq import HistoryFreqTracker
        HistoryFreqTracker._instance = None
        HistoryFreqTracker._initialized = False
        if os.path.exists(self.temp_db.name):
            try:
                os.unlink(self.temp_db.name)
            except PermissionError:
                pass

    def test_smart_completer_initialization(self):
        """Test SmartPGCompleter initialization."""
        from pgcli.completion.smart_completer import SmartPGCompleter

        completer = SmartPGCompleter(
            smart_completion=True,
            smart_completion_enabled=True,
            history_freq_db_path=self.temp_db.name
        )

        assert completer.smart_completion_enabled is True
        assert completer._history_tracker is not None

    def test_smart_completer_disabled_by_default(self):
        """Test that smart completion is disabled by default."""
        from pgcli.completion.smart_completer import SmartPGCompleter

        completer = SmartPGCompleter(smart_completion=True)

        assert completer.smart_completion_enabled is False
        assert completer._history_tracker is None

    def test_enable_smart_completion(self):
        """Test enabling smart completion at runtime."""
        from pgcli.completion.smart_completer import SmartPGCompleter

        completer = SmartPGCompleter(smart_completion=True, smart_completion_enabled=False)

        assert completer.smart_completion_enabled is False

        completer.enable_smart_completion(True)

        assert completer.smart_completion_enabled is True

    def test_update_history_from_query(self):
        """Test updating history from a SQL query."""
        from pgcli.completion.smart_completer import SmartPGCompleter

        completer = SmartPGCompleter(
            smart_completion=True,
            smart_completion_enabled=True,
            history_freq_db_path=self.temp_db.name
        )

        completer.update_history_from_query("SELECT * FROM users WHERE id = 1")

        # Should have recorded SELECT
        assert completer._history_tracker.get_frequency("SELECT") >= 1

    def test_record_completion_usage(self):
        """Test recording completion usage."""
        from pgcli.completion.smart_completer import SmartPGCompleter

        completer = SmartPGCompleter(
            smart_completion=True,
            smart_completion_enabled=True,
            history_freq_db_path=self.temp_db.name
        )

        completer.record_completion_usage("SELECT", "keyword")

        assert completer._history_tracker.get_frequency("SELECT") >= 1
