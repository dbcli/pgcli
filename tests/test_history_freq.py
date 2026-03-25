import os
import tempfile
import pytest
from pgcli.packages.history_freq import HistoryFrequencyManager, SmartCompletionSorter, get_history_freq_db_path


class TestHistoryFrequencyManager:
    def test_get_history_freq_db_path(self):
        path = get_history_freq_db_path()
        assert path.endswith("history_freq.db")
        assert "pgcli" in path.lower()

    def test_singleton_pattern(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_freq.db")
            try:
                manager1 = HistoryFrequencyManager(db_path)
                manager2 = HistoryFrequencyManager(db_path)
                assert manager1 is manager2
            finally:
                manager1.close()

    def test_record_and_get_keyword_frequency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_freq.db")
            manager = HistoryFrequencyManager(db_path)
            try:
                manager.clear_all()
                
                assert manager.get_keyword_frequency("SELECT") == 0
                
                manager.record_keyword_usage("SELECT")
                assert manager.get_keyword_frequency("SELECT") == 1
                
                manager.record_keyword_usage("SELECT")
                assert manager.get_keyword_frequency("SELECT") == 2
                
                manager.record_keyword_usage("select")
                assert manager.get_keyword_frequency("SELECT") == 3
            finally:
                manager.close()

    def test_record_keywords_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_freq.db")
            manager = HistoryFrequencyManager(db_path)
            try:
                manager.clear_all()
                
                manager.record_keywords_batch(["SELECT", "FROM", "WHERE"])
                assert manager.get_keyword_frequency("SELECT") == 1
                assert manager.get_keyword_frequency("FROM") == 1
                assert manager.get_keyword_frequency("WHERE") == 1
            finally:
                manager.close()

    def test_get_all_frequencies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_freq.db")
            manager = HistoryFrequencyManager(db_path)
            try:
                manager.clear_all()
                
                manager.record_keywords_batch(["SELECT", "SELECT", "FROM"])
                freqs = manager.get_all_frequencies()
                assert freqs["SELECT"] == 2
                assert freqs["FROM"] == 1
            finally:
                manager.close()

    def test_get_top_keywords(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_freq.db")
            manager = HistoryFrequencyManager(db_path)
            try:
                manager.clear_all()
                
                for _ in range(5):
                    manager.record_keyword_usage("SELECT")
                for _ in range(3):
                    manager.record_keyword_usage("FROM")
                manager.record_keyword_usage("WHERE")
                
                top = manager.get_top_keywords(2)
                assert len(top) == 2
                assert top[0][0] == "SELECT"
                assert top[0][1] == 5
                assert top[1][0] == "FROM"
                assert top[1][1] == 3
            finally:
                manager.close()

    def test_clear_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_freq.db")
            manager = HistoryFrequencyManager(db_path)
            try:
                manager.record_keyword_usage("SELECT")
                assert manager.get_keyword_frequency("SELECT") > 0
                
                manager.clear_all()
                assert manager.get_keyword_frequency("SELECT") == 0
            finally:
                manager.close()


class TestSmartCompletionSorter:
    def test_sort_keywords_by_frequency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_freq.db")
            manager = HistoryFrequencyManager(db_path)
            try:
                manager.clear_all()
                
                sorter = SmartCompletionSorter(manager)
                
                for _ in range(5):
                    manager.record_keyword_usage("SELECT")
                for _ in range(3):
                    manager.record_keyword_usage("FROM")
                manager.record_keyword_usage("WHERE")
                
                keywords = ["WHERE", "SELECT", "FROM", "JOIN"]
                sorted_keywords = sorter.sort_keywords_by_frequency(keywords)
                
                assert sorted_keywords[0] == "SELECT"
                assert sorted_keywords[1] == "FROM"
                assert sorted_keywords[2] == "WHERE"
            finally:
                manager.close()

    def test_get_frequency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_freq.db")
            manager = HistoryFrequencyManager(db_path)
            try:
                manager.clear_all()
                
                sorter = SmartCompletionSorter(manager)
                
                manager.record_keyword_usage("SELECT")
                manager.record_keyword_usage("SELECT")
                
                assert sorter.get_frequency("SELECT") == 2
                assert sorter.get_frequency("NONEXISTENT") == 0
            finally:
                manager.close()
