import re
import sqlparse
from sqlparse.tokens import Name
from collections import defaultdict
from .pgliterals.main import get_literals


white_space_regex = re.compile("\\s+", re.MULTILINE)


def _compile_regex(keyword):
    pattern = "\\b" + white_space_regex.sub(r"\\s+", keyword) + "\\b"
    return re.compile(pattern, re.MULTILINE | re.IGNORECASE)


keywords = get_literals("keywords")
keyword_regexs = {kw: _compile_regex(kw) for kw in keywords}


class PrevalenceCounter:
    def __init__(self, smart_completion_freq=False):
        self.keyword_counts = defaultdict(int)
        self.name_counts = defaultdict(int)
        self.smart_completion_freq = smart_completion_freq
        self._history_freq_manager = None
        if smart_completion_freq:
            try:
                from .history_freq import HistoryFrequencyManager
                self._history_freq_manager = HistoryFrequencyManager()
            except Exception:
                self._history_freq_manager = None

    def set_smart_completion_freq(self, enabled):
        self.smart_completion_freq = enabled
        if enabled and self._history_freq_manager is None:
            try:
                from .history_freq import HistoryFrequencyManager
                self._history_freq_manager = HistoryFrequencyManager()
            except Exception:
                self._history_freq_manager = None

    def update(self, text):
        self.update_keywords(text)
        self.update_names(text)

    def update_names(self, text):
        for parsed in sqlparse.parse(text):
            for token in parsed.flatten():
                if token.ttype in Name:
                    self.name_counts[token.value] += 1

    def clear_names(self):
        self.name_counts = defaultdict(int)

    def update_keywords(self, text):
        found_keywords = []
        for keyword, regex in keyword_regexs.items():
            for _ in regex.finditer(text):
                self.keyword_counts[keyword] += 1
                found_keywords.append(keyword)
        if self.smart_completion_freq and self._history_freq_manager and found_keywords:
            self._history_freq_manager.record_keywords_batch(found_keywords)

    def keyword_count(self, keyword):
        session_count = self.keyword_counts[keyword]
        if self.smart_completion_freq and self._history_freq_manager:
            history_count = self._history_freq_manager.get_keyword_frequency(keyword)
            return session_count + history_count
        return session_count

    def name_count(self, name):
        return self.name_counts[name]

    def record_keyword_selection(self, keyword):
        if self.smart_completion_freq and self._history_freq_manager:
            self._history_freq_manager.record_keyword_usage(keyword)
