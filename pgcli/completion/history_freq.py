"""
History frequency tracker for smart SQL completion.

This module tracks SQL keyword usage frequency and stores it in a SQLite database
to enable intelligent completion sorting based on user habits.
"""

import os
import sqlite3
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from ..config import config_location

_logger = logging.getLogger(__name__)


class HistoryFreqTracker:
    """
    Tracks SQL keyword usage frequency using SQLite backend.

    Stores usage statistics in ~/.config/pgcli/history_freq.db
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return

        if db_path is None:
            db_path = self._get_default_db_path()

        self.db_path = db_path
        self._local = threading.local()
        self._ensure_db_exists()
        self._initialized = True
        _logger.debug("HistoryFreqTracker initialized with db: %s", self.db_path)

    @staticmethod
    def _get_default_db_path() -> str:
        """Get the default database path."""
        config_dir = config_location()
        return os.path.join(config_dir, "history_freq.db")

    def _ensure_db_exists(self):
        """Ensure the database file and schema exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Create keyword frequency table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_frequency (
                    keyword TEXT PRIMARY KEY,
                    count INTEGER NOT NULL DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create completion usage table for tracking which completions were selected
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS completion_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    completion_text TEXT NOT NULL,
                    completion_type TEXT,
                    context TEXT,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_completion_usage_text
                ON completion_usage(completion_text)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_completion_usage_time
                ON completion_usage(used_at)
            """)

            conn.commit()
        except sqlite3.Error as e:
            _logger.error("Error creating history_freq database schema: %s", e)
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def record_usage(self, keyword: str, count: int = 1):
        """
        Record usage of a keyword.

        Args:
            keyword: The SQL keyword or completion text used
            count: Number of times to increment (default 1)
        """
        if not keyword:
            return

        keyword = keyword.upper().strip()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO keyword_frequency (keyword, count, last_used)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(keyword) DO UPDATE SET
                    count = count + ?,
                    last_used = CURRENT_TIMESTAMP
            """, (keyword, count, count))

            conn.commit()
        except sqlite3.Error as e:
            _logger.error("Error recording keyword usage: %s", e)

    def record_completion_selection(self, completion_text: str, completion_type: Optional[str] = None, context: Optional[str] = None):
        """
        Record that a completion was selected by the user.

        Args:
            completion_text: The text that was selected
            completion_type: Type of completion (keyword, table, column, etc.)
            context: Optional context (e.g., SQL statement type)
        """
        if not completion_text:
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO completion_usage (completion_text, completion_type, context)
                VALUES (?, ?, ?)
            """, (completion_text, completion_type, context))

            conn.commit()

            # Also update the keyword frequency
            self.record_usage(completion_text)

        except sqlite3.Error as e:
            _logger.error("Error recording completion selection: %s", e)

    def get_frequency(self, keyword: str) -> int:
        """
        Get the usage frequency of a keyword.

        Args:
            keyword: The keyword to look up

        Returns:
            The usage count (0 if not found)
        """
        if not keyword:
            return 0

        keyword = keyword.upper().strip()

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT count FROM keyword_frequency WHERE keyword = ?",
                (keyword,)
            )
            row = cursor.fetchone()

            return row[0] if row else 0

        except sqlite3.Error as e:
            _logger.error("Error getting keyword frequency: %s", e)
            return 0

    def get_all_frequencies(self) -> Dict[str, int]:
        """
        Get all keyword frequencies.

        Returns:
            Dictionary mapping keywords to their usage counts
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT keyword, count FROM keyword_frequency")
            rows = cursor.fetchall()

            return {row[0]: row[1] for row in rows}

        except sqlite3.Error as e:
            _logger.error("Error getting all frequencies: %s", e)
            return {}

    def get_top_keywords(self, limit: int = 100, completion_type: Optional[str] = None) -> List[Tuple[str, int]]:
        """
        Get the most frequently used keywords.

        Args:
            limit: Maximum number of results
            completion_type: Optional filter by completion type

        Returns:
            List of (keyword, count) tuples sorted by count descending
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if completion_type:
                cursor.execute("""
                    SELECT completion_text, COUNT(*) as cnt
                    FROM completion_usage
                    WHERE completion_type = ?
                    GROUP BY completion_text
                    ORDER BY cnt DESC
                    LIMIT ?
                """, (completion_type, limit))
            else:
                cursor.execute("""
                    SELECT keyword, count
                    FROM keyword_frequency
                    ORDER BY count DESC, last_used DESC
                    LIMIT ?
                """, (limit,))

            return [(row[0], row[1]) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            _logger.error("Error getting top keywords: %s", e)
            return []

    def clear_history(self):
        """Clear all history data."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM keyword_frequency")
            cursor.execute("DELETE FROM completion_usage")

            conn.commit()
            _logger.info("History frequency data cleared")

        except sqlite3.Error as e:
            _logger.error("Error clearing history: %s", e)

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the history database.

        Returns:
            Dictionary with statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM keyword_frequency")
            keyword_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM completion_usage")
            completion_count = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(count) FROM keyword_frequency")
            total_usage = cursor.fetchone()[0] or 0

            return {
                "unique_keywords": keyword_count,
                "total_completions": completion_count,
                "total_usage": total_usage,
            }

        except sqlite3.Error as e:
            _logger.error("Error getting stats: %s", e)
            return {"unique_keywords": 0, "total_completions": 0, "total_usage": 0}

    def close(self):
        """Close the database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    def __del__(self):
        """Cleanup on deletion."""
        self.close()


# Global instance cache
_history_freq_tracker = None
_history_freq_lock = threading.Lock()


def get_history_freq_tracker(db_path: Optional[str] = None) -> HistoryFreqTracker:
    """
    Get the global HistoryFreqTracker instance.

    Args:
        db_path: Optional custom database path

    Returns:
        HistoryFreqTracker instance
    """
    global _history_freq_tracker

    if _history_freq_tracker is None:
        with _history_freq_lock:
            if _history_freq_tracker is None:
                _history_freq_tracker = HistoryFreqTracker(db_path)

    return _history_freq_tracker


def reset_history_freq_tracker():
    """Reset the global tracker instance (useful for testing)."""
    global _history_freq_tracker
    with _history_freq_lock:
        if _history_freq_tracker:
            _history_freq_tracker.close()
        _history_freq_tracker = None
