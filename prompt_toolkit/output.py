"""
Interface for an output.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'Output',
)


class Output(with_metaclass(ABCMeta, object)):
    """
    Base class defining the output interface for a
    :class:`~prompt_toolkit.renderer.Renderer`.

    Actual implementations are
    :class:`~prompt_toolkit.terminal.vt100_output.Vt100_Output` and
    :class:`~prompt_toolkit.terminal.win32_output.Win32Output`.
    """
    @abstractmethod
    def write(self, data):
        " Write text. "

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
        " Go to the alternate screen buffer. (For full screen applications). "

    @abstractmethod
    def quit_alternate_screen(self):
        " Leave the alternate screen buffer. "

    @abstractmethod
    def enable_mouse_support(self):
        " Enable mouse. "

    @abstractmethod
    def disable_mouse_support(self):
        " Disable mouse. "

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
        " Reset color and styling attributes. "

    @abstractmethod
    def set_attributes(self, attrs):
        " Set new color and styling attributes. "

    @abstractmethod
    def disable_autowrap(self):
        " Disable auto line wrapping. "

    @abstractmethod
    def enable_autowrap(self):
        " Enable auto line wrapping. "

    @abstractmethod
    def cursor_goto(self, row=0, column=0):
        " Move cursor position. "

    @abstractmethod
    def cursor_up(self, amount):
        " Move cursor `amount` place up. "

    @abstractmethod
    def cursor_down(self, amount):
        " Move cursor `amount` place down. "

    @abstractmethod
    def cursor_forward(self, amount):
        " Move cursor `amount` place forward. "

    @abstractmethod
    def cursor_backward(self, amount):
        " Move cursor `amount` place backward. "

    def ask_for_cpr(self):
        """
        Asks for a cursor position report (CPR).
        (VT100 only.)
        """
