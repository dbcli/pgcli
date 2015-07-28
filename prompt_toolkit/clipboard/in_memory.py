from .base import Clipboard, ClipboardData

__all__ = (
    'InMemoryClipboard',
)


class InMemoryClipboard(Clipboard):
    """
    Default clipboard implementation.
    Just keep the data in memory.
    """
    def __init__(self):
        self._data = None

    def set_data(self, data):
        assert isinstance(data, ClipboardData)
        self._data = data

    def get_data(self):
        return self._data or ClipboardData()
