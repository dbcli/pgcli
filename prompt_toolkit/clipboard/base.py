"""
Clipboard for command line interface.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass
import six

from prompt_toolkit.selection import SelectionType

__all__ = [
    'Clipboard',
    'ClipboardData',
    'DummyClipboard',
    'DynamicClipboard',
]


class ClipboardData(object):
    """
    Text on the clipboard.

    :param text: string
    :param type: :class:`~prompt_toolkit.selection.SelectionType`
    """
    def __init__(self, text='', type=SelectionType.CHARACTERS):
        assert isinstance(text, six.string_types)
        assert type in (SelectionType.CHARACTERS, SelectionType.LINES, SelectionType.BLOCK)

        self.text = text
        self.type = type


class Clipboard(with_metaclass(ABCMeta, object)):
    """
    Abstract baseclass for clipboards.
    (An implementation can be in memory, it can share the X11 or Windows
    keyboard, or can be persistent.)
    """
    @abstractmethod
    def set_data(self, data):
        """
        Set data to the clipboard.

        :param data: :class:`~.ClipboardData` instance.
        """

    def set_text(self, text):  # Not abstract.
        """
        Shortcut for setting plain text on clipboard.
        """
        assert isinstance(text, six.string_types)
        self.set_data(ClipboardData(text))

    def rotate(self):
        """
        For Emacs mode, rotate the kill ring.
        """

    @abstractmethod
    def get_data(self):
        """
        Return clipboard data.
        """


class DummyClipboard(Clipboard):
    """
    Clipboard implementation that doesn't remember anything.
    """
    def set_data(self, data):
        pass

    def set_text(self, text):
        pass

    def rotate(self):
        pass

    def get_data(self):
        return ClipboardData()


class DynamicClipboard(Clipboard):
    """
    Clipboard class that can dynamically returns any Clipboard.

    :param get_clipboard: Callable that returns a :class:`.Clipboard` instance.
    """
    def __init__(self, get_clipboard):
        assert callable(get_clipboard)
        self.get_clipboard = get_clipboard

    def _clipboard(self):
        clipboard = self.get_clipboard() or DummyClipboard()
        assert isinstance(clipboard, Clipboard)
        return clipboard

    def set_data(self, data):
        self._clipboard().set_data(data)

    def set_text(self, text):
        self._clipboard().set_text(text)

    def rotate(self):
        self._clipboard().rotate()

    def get_data(self):
        return self._clipboard().get_data()
