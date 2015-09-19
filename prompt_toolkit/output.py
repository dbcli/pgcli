"""
Interface for an output.

The actual implementations are in
`prompt_toolkit.terminal.vt100_output/win32_output`.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'Output',
)


class Output(with_metaclass(ABCMeta, object)):
    """
    Base class defining the Output interface for a renderer.
    """
    @abstractmethod
    def write(self, data):
        pass

    @abstractmethod
    def set_title(self, title):
        " Set terminal title. "

    @abstractmethod
    def clear_title(self):
        " Clear title again. (or restore previous title.) "

    @abstractmethod
    def flush(self):
        " Write to output stream and flush. "

    @abstractmethod
    def erase_screen(self):
        """
        Erases the screen with the background colour and moves the cursor to
        home.
        """

    @abstractmethod
    def enter_alternate_screen(self):
        pass

    @abstractmethod
    def quit_alternate_screen(self):
        pass

    @abstractmethod
    def enable_mouse_support(self):
        pass

    @abstractmethod
    def disable_mouse_support(self):
        pass

    @abstractmethod
    def erase_end_of_line(self):
        """
        Erases from the current cursor position to the end of the current line.
        """

    @abstractmethod
    def erase_down(self):
        """
        Erases the screen from the current line down to the bottom of the
        screen.
        """

    @abstractmethod
    def reset_attributes(self):
        pass

    @abstractmethod
    def set_attributes(self, fgcolor=None, bgcolor=None, bold=False, underline=False):
        """
        Create new style and output.
        """
        pass

    @abstractmethod
    def disable_autowrap(self):
        pass

    @abstractmethod
    def enable_autowrap(self):
        pass

    @abstractmethod
    def cursor_goto(self, row=0, column=0):
        """ Move cursor position. """

    @abstractmethod
    def cursor_up(self, amount):
        pass

    @abstractmethod
    def cursor_down(self, amount):
        pass

    @abstractmethod
    def cursor_forward(self, amount):
        pass

    @abstractmethod
    def cursor_backward(self, amount):
        pass

    def ask_for_cpr(self):
        """
        Asks for a cursor position report (CPR).
        (VT100 only.)
        """
