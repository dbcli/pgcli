import os
import sqlite3
import threading
from collections import defaultdict
from contextlib import contextmanager


def get_history_freq_db_path():
    if "XDG_CONFIG_HOME" in os.environ:
        base_path = os.path.expanduser(os.environ["XDG_CONFIG_HOME"])
        return os.path.join(base_path, "pgcli", "history_freq.db")
    elif os.name == "nt":
        base_path = os.getenv("USERPROFILE", "")
        return os.path.join(base_path, "AppData", "Local", "dbcli", "pgcli", "history_freq.db")
    else:
        return os.path.expanduser("~/.config/pgcli/history_freq.db")


class HistoryFrequencyManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path=None):
        if self._initialized:
            return
        self._initialized = True
        self.db_path = db_path or get_history_freq_db_path()
        self._local = threading.local()
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self):
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    @contextmanager
    def _get_cursor(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _init_db(self):
        with self._get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_frequency (
                    keyword TEXT PRIMARY KEY,
                    frequency INTEGER DEFAULT 0,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keyword_frequency 
                ON keyword_frequency(frequency DESC)
            """)

    def record_keyword_usage(self, keyword):
        if not keyword or not isinstance(keyword, str):
            return
        keyword = keyword.upper().strip()
        if not keyword:
            return
        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO keyword_frequency (keyword, frequency, last_used)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(keyword) DO UPDATE SET 
                    frequency = frequency + 1,
                    last_used = CURRENT_TIMESTAMP
            """, (keyword,))

    def record_keywords_batch(self, keywords):
        if not keywords:
            return
        keyword_counts = defaultdict(int)
        for keyword in keywords:
            if keyword and isinstance(keyword, str):
                kw = keyword.upper().strip()
                if kw:
                    keyword_counts[kw] += 1
        if not keyword_counts:
            return
        with self._get_cursor() as cursor:
            for keyword, count in keyword_counts.items():
                cursor.execute("""
                    INSERT INTO keyword_frequency (keyword, frequency, last_used)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(keyword) DO UPDATE SET 
                        frequency = frequency + ?,
                        last_used = CURRENT_TIMESTAMP
                """, (keyword, count, count))

    def get_keyword_frequency(self, keyword):
        if not keyword:
            return 0
        keyword = keyword.upper().strip()
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT frequency FROM keyword_frequency WHERE keyword = ?
            """, (keyword,))
            row = cursor.fetchone()
            return row["frequency"] if row else 0

    def get_all_frequencies(self):
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT keyword, frequency FROM keyword_frequency ORDER BY frequency DESC
            """)
            return {row["keyword"]: row["frequency"] for row in cursor.fetchall()}

    def get_top_keywords(self, limit=100):
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT keyword, frequency FROM keyword_frequency 
                ORDER BY frequency DESC LIMIT ?
            """, (limit,))
            return [(row["keyword"], row["frequency"]) for row in cursor.fetchall()]

    def clear_all(self):
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM keyword_frequency")

    def close(self):
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
        HistoryFrequencyManager._instance = None
        self._initialized = False


class SmartCompletionSorter:
    def __init__(self, history_manager=None):
        self.history_manager = history_manager or HistoryFrequencyManager()
        self._frequency_cache = {}
        self._cache_valid = False

    def _ensure_cache(self):
        if not self._cache_valid:
            self._frequency_cache = self.history_manager.get_all_frequencies()
            self._cache_valid = False

    def record_and_sort_keywords(self, selected_keyword, all_keywords):
        self.history_manager.record_keyword_usage(selected_keyword)
        self._cache_valid = False
        return self.sort_keywords_by_frequency(all_keywords)

    def sort_keywords_by_frequency(self, keywords):
        self._ensure_cache()
        freq = self._frequency_cache
        return sorted(keywords, key=lambda k: (-freq.get(k.upper(), 0), k.lower()))

    def get_frequency(self, keyword):
        self._ensure_cache()
        return self._frequency_cache.get(keyword.upper(), 0)

    def invalidate_cache(self):
        self._cache_valid = False
