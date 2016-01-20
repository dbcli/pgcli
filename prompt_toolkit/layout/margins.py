"""
Margin implementations for a :class:`~prompt_toolkit.layout.containers.Window`.
"""
from __future__ import unicode_literals

from six import with_metaclass
from abc import ABCMeta, abstractmethod

from prompt_toolkit.filters import to_cli_filter
from prompt_toolkit.token import Token
from prompt_toolkit.utils import get_cwidth

__all__ = (
    'Margin',
    'NumberredMargin',
    'ScrollbarMargin',
    'ConditionalMargin',
    'PromptMargin',
)


class Margin(with_metaclass(ABCMeta, object)):
    """
    Base interface for a margin.
    """
    @abstractmethod
    def get_width(self, cli):
        """
        Return the width that this margin is going to consume.
        """
        return 0

    @abstractmethod
    def create_margin(self, cli, window_render_info, width, height):
        """
        Creates a margin.
        This should return a list of (Token, text) tuples.

        :param window_render_info:
            :class:`~prompt_toolkit.layout.containers.WindowRenderInfo`
            instance, generated after rendering and copying the visible part of
            the :class:`~prompt_toolkit.layout.controls.UIControl` into the
            :class:`~prompt_toolkit.layout.containers.Window`.
        :param width: The width that's available for this margin. (As reported
            by :meth:`.get_width`.)
        :param height: The height that's available for this margin. (The height
            of the :class:`~prompt_toolkit.layout.containers.Window`.)
        """
        return []


class NumberredMargin(Margin):
    """
    Margin that displays the line numbers.

    :param buffer_name: The name of the buffer. This is recommended if the
        margin is used together with a
        :class:`~prompt_toolkit.layout.controls.BufferControl` inside a
        :class:`~prompt_toolkit.layout.containers.Window`. That way, we can
        predict the width of this margin (the amount of decimals) according to
        the number of lines in the buffer.
    :param width: If no buffer name is given, width can be used to set a fixed
        width.
    :param relative: Number relative to the cursor position. Similar to the Vi
                     'relativenumber' option.
    """
    def __init__(self, buffer_name=None, width=None, relative=False):
        assert buffer_name or width

        self.buffer_name = buffer_name
        self.width = width
        self.relative = to_cli_filter(relative)

    def get_width(self, cli):
        if self.width is not None:
            # Fixed width.
            return self.width
        else:
            # Width determined by the amount of lines in the buffer.
            document = cli.buffers[self.buffer_name].document
            return max(3, len('%s' % document.line_count) + 1)

    def create_margin(self, cli, window_render_info, width, height):
        visible_line_to_input_line = window_render_info.visible_line_to_input_line
        relative = self.relative(cli)

        token = Token.LineNumber
        token_current = Token.LineNumber.Current

        # Get current line number.
        if self.buffer_name:
            # (BufferControl will only have a cursor position when the buffer
            # has the focus, so this is a better way to know the current line.)
            document = cli.buffers[self.buffer_name].document
            current_lineno = document.cursor_position_row
        else:
            current_lineno = visible_line_to_input_line.get(window_render_info.cursor_position.y) or 0

        # Construct margin.
        result = []

        for y in range(window_render_info.window_height):
            line_number = visible_line_to_input_line.get(y)

            if line_number is not None:
                if line_number == current_lineno:
                    # Current line.
                    if relative:
                        # Left align current number in relative mode.
                        result.append((token_current, '%i' % (line_number + 1)))
                    else:
                        result.append((token_current, ('%i ' % (line_number + 1)).rjust(width)))
                else:
                    # Other lines.
                    if relative:
                        line_number = abs(line_number - current_lineno) - 1

                    result.append((token, ('%i ' % (line_number + 1)).rjust(width)))

            result.append((Token, '\n'))

        return result


class ConditionalMargin(Margin):
    """
    Wrapper around other :class:`.Margin` classes to show/hide them.
    """
    def __init__(self, margin, filter):
        assert isinstance(margin, Margin)

        self.margin = margin
        self.filter = to_cli_filter(filter)

    def get_width(self, cli):
        if self.filter(cli):
            return self.margin.get_width(cli)
        else:
            return 0

    def create_margin(self, cli, window_render_info, width, height):
        if width and self.filter(cli):
            return self.margin.create_margin(cli, window_render_info, width, height)
        else:
            return []


class ScrollbarMargin(Margin):
    """
    Margin displaying a scrollbar.
    """
    def get_width(self, cli):
        return 1

    def create_margin(self, cli, window_render_info, width, height):
        total_height = window_render_info.content_height
        items_per_row = float(total_height) / min(total_height, window_render_info.window_height - 2)

        index = window_render_info.vertical_scroll

        visible_lines = set(range(index, index + window_render_info.window_height))

        def is_scroll_button(row):
            " True if we should display a button on this row. "
            current_row_middle = int((row + .5) * items_per_row)
            return current_row_middle in visible_lines

        # Generate tokens.
        result = [
            (Token.Scrollbar.Arrow, '\u25b2'),  # Up arrow.
            (Token.Scrollbar, '\n')
        ]

        for i in range(window_render_info.window_height - 2):
            if is_scroll_button(i):
                result.append((Token.Scrollbar.Button, ' '))
            else:
                result.append((Token.Scrollbar, ' '))
            result.append((Token, '\n'))

        result.append((Token.Scrollbar.Arrow, '\u25bc'))  # Down arrow

        return result


class PromptMargin(Margin):
    """
    Create margin that displays a prompt.
    This can display one prompt at the first line, and a continuation prompt
    (e.g, just dots) on all the following lines.

    :param get_prompt_tokens: Callable that takes a CommandLineInterface as
        input and returns a list of (Token, type) tuples to be shown as the
        prompt at the first line.
    :param get_continuation_tokens: Callable that takes a CommandLineInterface
        and a width as input and returns a list of (Token, type) tuples for the
        next lines of the input.
    :param show_numbers: (bool or :class:`~prompt_toolkit.filters.CLIFilter`)
        Display line numbers instead of the continuation prompt.
    """
    def __init__(self, get_prompt_tokens, get_continuation_tokens=None,
                 show_numbers=False):
        assert callable(get_prompt_tokens)
        assert get_continuation_tokens is None or callable(get_continuation_tokens)
        show_numbers = to_cli_filter(show_numbers)

        self.get_prompt_tokens = get_prompt_tokens
        self.get_continuation_tokens = get_continuation_tokens
        self.show_numbers = show_numbers

    def get_width(self, cli):
        " Width to report to the `Window`. "
        # Take the width from the first line.
        text = ''.join(t[1] for t in self.get_prompt_tokens(cli))
        return get_cwidth(text)

    def create_margin(self, cli, window_render_info, width, height):
        # First line.
        tokens = self.get_prompt_tokens(cli)[:]

        # Next lines. (Show line numbering when numbering is enabled.)
        if self.get_continuation_tokens:
            tokens2 = self.get_continuation_tokens(cli, width)
        else:
            tokens2 = []

        show_numbers = self.show_numbers(cli)
        visible_line_to_input_line = window_render_info.visible_line_to_input_line

        for y in range(1, min(window_render_info.content_height, height)):
            tokens.append((Token, '\n'))
            if show_numbers:
                line_number = visible_line_to_input_line.get(y) or 0
                tokens.append((Token.LineNumber, ('%i ' % (line_number + 1)).rjust(width)))
            else:
                tokens.extend(tokens2)

        return tokens
