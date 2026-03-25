import sqlite3
import os
import platform
import re
import sqlparse
from sqlparse.tokens import Name
from os.path import expanduser
from .pgliterals.main import get_literals


white_space_regex = re.compile("\\s+", re.MULTILINE)


def _compile_regex(keyword):
    # Surround the keyword with word boundaries and replace interior whitespace
    # with whitespace wildcards
    pattern = "\\b" + white_space_regex.sub(r"\\s+", keyword) + "\\b"
    return re.compile(pattern, re.MULTILINE | re.IGNORECASE)


keywords = get_literals("keywords")
keyword_regexs = {kw: _compile_regex(kw) for kw in keywords}


def history_freq_location():
    """Return the path to the history frequency database location."""
    if "XDG_DATA_HOME" in os.environ:
        return "%s/pgcli/history_freq.db" % expanduser(os.environ["XDG_DATA_HOME"])
    elif platform.system() == "Windows":
        return os.getenv("USERPROFILE") + "\\AppData\\Local\\dbcli\\pgcli\\history_freq.db"
    else:
        return expanduser("~/.local/share/pgcli/history_freq.db")


class HistoryFrequency:
    def __init__(self, db_path=None):
        """Initialize the history frequency tracker.
        :param db_path: path to the SQLite database file.
        """
        self.db_path = db_path or history_freq_location()
        self.conn = None
        
        # For in-memory databases, we need to keep the connection open
        if self.db_path == ":memory:":
            self.conn = sqlite3.connect(self.db_path)
            self._create_table(self.conn)
        else:
            self._create_table()

    def _create_table(self, conn=None):
        """Create the frequency tables if they don't exist."""
        # Ensure directory exists (skip for in-memory databases)
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            with conn:
                self._create_tables_on_conn(conn)
            conn.close()
        else:
            self._create_tables_on_conn(conn)

    def _create_tables_on_conn(self, conn):
        """Create tables on the given connection."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS keyword_frequency (
                keyword TEXT PRIMARY KEY,
                frequency INTEGER DEFAULT 1,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS name_frequency (
                name TEXT PRIMARY KEY,
                frequency INTEGER DEFAULT 1,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _get_connection(self):
        """Get a database connection."""
        if self.db_path == ":memory:":
            return self.conn
        return sqlite3.connect(self.db_path)

    def _close_connection(self, conn):
        """Close the connection unless it's an in-memory database."""
        if self.db_path != ":memory:":
            conn.close()

    def increment_keyword(self, keyword):
        """Increment the frequency count for a keyword."""
        keyword = keyword.lower()
        conn = self._get_connection()
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO keyword_frequency (keyword, frequency, last_used)
                VALUES (
                    ?,
                    COALESCE((SELECT frequency FROM keyword_frequency WHERE keyword = ?), 0) + 1,
                    CURRENT_TIMESTAMP
                )
            """, (keyword, keyword))
        self._close_connection(conn)

    def increment_name(self, name):
        """Increment the frequency count for a name/identifier."""
        name = name.lower()
        conn = self._get_connection()
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO name_frequency (name, frequency, last_used)
                VALUES (
                    ?,
                    COALESCE((SELECT frequency FROM name_frequency WHERE name = ?), 0) + 1,
                    CURRENT_TIMESTAMP
                )
            """, (name, name))
        self._close_connection(conn)

    def get_keyword_frequency(self, keyword):
        """Get the frequency count for a keyword."""
        keyword = keyword.lower()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT frequency FROM keyword_frequency WHERE keyword = ?", (keyword,))
        result = cursor.fetchone()
        self._close_connection(conn)
        return result[0] if result else 0

    def get_name_frequency(self, name):
        """Get the frequency count for a name/identifier."""
        name = name.lower()
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT frequency FROM name_frequency WHERE name = ?", (name,))
        result = cursor.fetchone()
        self._close_connection(conn)
        return result[0] if result else 0

    def update_from_text(self, text):
        """Update frequencies from SQL text by extracting keywords and names."""
        self.update_keywords(text)
        self.update_names(text)

    def update_keywords(self, text):
        """Update keyword frequencies from SQL text."""
        for keyword, regex in keyword_regexs.items():
            count = len(list(regex.finditer(text)))
            if count > 0:
                keyword_lower = keyword.lower()
                conn = self._get_connection()
                with conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO keyword_frequency (keyword, frequency, last_used)
                        VALUES (
                            ?,
                            COALESCE((SELECT frequency FROM keyword_frequency WHERE keyword = ?), 0) + ?,
                            CURRENT_TIMESTAMP
                        )
                    """, (keyword_lower, keyword_lower, count))
                self._close_connection(conn)

    def update_names(self, text):
        """Update name/identifier frequencies from SQL text."""
        for parsed in sqlparse.parse(text):
            for token in parsed.flatten():
                if token.ttype in Name:
                    name_lower = token.value.lower()
                    conn = self._get_connection()
                    with conn:
                        conn.execute("""
                            INSERT OR REPLACE INTO name_frequency (name, frequency, last_used)
                            VALUES (
                                ?,
                                COALESCE((SELECT frequency FROM name_frequency WHERE name = ?), 0) + 1,
                                CURRENT_TIMESTAMP
                            )
                        """, (name_lower, name_lower))
                    self._close_connection(conn)

    def clear(self):
        """Clear all frequency data."""
        conn = self._get_connection()
        with conn:
            conn.execute("DELETE FROM keyword_frequency")
            conn.execute("DELETE FROM name_frequency")
        self._close_connection(conn)