"""
Clipboard for command line interface.
"""
from __future__ import unicode_literals
import six

from .selection import SelectionType

__all__ = (
    'Clipboard',
    'ClipboardData',
)


class ClipboardData(object):
    """
    Text on the clipboard.

    :param text: string
    :param type: :class:`~.ClipboardDataType`
    """
    def __init__(self, text='', type=SelectionType.CHARACTERS):
        assert isinstance(text, six.string_types)
        assert type in (SelectionType.CHARACTERS, SelectionType.LINES)

        self.text = text
        self.type = type


class Clipboard(object):
    """
    Clipboard for command line interface.
    """
    def __init__(self):
        self._data = None

    def set_data(self, data):
        """
        Set data to the clipboard.

        :param data: :class:`~.ClipboardData` instance.
        """
        assert isinstance(data, ClipboardData)

        if data.text:
            self._data = data

    def set_text(self, text):
        assert isinstance(text, six.string_types)

        if text:
            self._data = ClipboardData(text)

    def get_data(self):
        return self._data or ClipboardData()
