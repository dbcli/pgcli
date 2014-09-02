"""
"""
from __future__ import unicode_literals

import re

__all__ = ('Document',)


# Regex for finding the "words" in documents. (We consider a group of alnum
# characters a word, but also a group of special characters a word, as long as
# it doesn't contain a space.)
_FIND_WORD_RE =  re.compile('([a-zA-Z0-9_]+|[^a-zA-Z0-9_\s]+)')


class Document(object):
    """
    This is a immutable class around the text and cursor position, and contains
    methods for querying this data, e.g. to give the text before the cursor.

    This class is usually instantiated by a :class:`~prompt_toolkit.line.Line`
    object, and accessed as the `document` property of that class.

    :param text: string
    :param cursor_position: int
    """
    __slots__ = ('text', 'cursor_position')

    def __init__(self, text='', cursor_position=0):
        self.text = text
        self.cursor_position = cursor_position

    @property
    def current_char(self):
        """ Return character under cursor, or None """
        return self._get_char_relative_to_cursor(0)

    @property
    def char_before_cursor(self):
        """ Return character before the cursor, or None """
        return self._get_char_relative_to_cursor(-1)

    @property
    def text_before_cursor(self):
        return self.text[:self.cursor_position:]

    @property
    def text_after_cursor(self):
        return self.text[self.cursor_position:]

    @property
    def current_line_before_cursor(self):
        """ Text from the start of the line until the cursor. """
        return self.text_before_cursor.split('\n')[-1]

    @property
    def current_line_after_cursor(self):
        """ Text from the cursor until the end of the line. """
        return self.text_after_cursor.split('\n')[0]

    @property
    def lines(self):
        """
        Array of all the lines.
        """
        return self.text.split('\n')

    @property
    def lines_from_current(self):
        """
        Array of the lines starting from the current line, until the last line.
        """
        return self.lines[self.cursor_position_row:]

    @property
    def line_count(self):
        """ Return the number of lines in this document. If the document ends
        with a trailing \n, that counts as the beginning of a new line. """
        return len(self.lines)

    @property
    def current_line(self):
        """ Return the text on the line where the cursor is. (when the input
        consists of just one line, it equals `text`. """
        return self.current_line_before_cursor + self.current_line_after_cursor

    @property
    def leading_whitespace_in_current_line(self):
        """ The leading whitespace in the left margin of the current line.  """
        current_line = self.current_line
        length = len(current_line) - len(current_line.lstrip())
        return current_line[:length]

    def _get_char_relative_to_cursor(self, offset=0):
        """ Return character relative to cursor position, or None """
        try:
            return self.text[self.cursor_position + offset]
        except IndexError:
            return None

    @property
    def cursor_position_row(self):
        """
        Current row. (0-based.)
        """
        return len(self.text_before_cursor.split('\n')) - 1

    @property
    def cursor_position_col(self):
        """
        Current column. (0-based.)
        """
        return len(self.current_line_before_cursor)

    def translate_index_to_position(self, index):
        """
        Given an index for the text, return the corresponding (row, col) tuple.
        """
        text_before_position = self.text[:index]

        row = len(text_before_position.split('\n'))
        col = len(text_before_position.split('\n')[-1])

        return row, col

    def translate_row_col_to_index(self, row, col): # TODO: unit test
        """
        Given a (row, col) tuple, return the corresponding index.
        (Row and col params are 0-based.)
        """
        return len('\n'.join(self.lines[:row])) + len('\n') + col

    @property
    def cursor_up_position(self):
        """
        Return the cursor position (character index) where we would be if the
        user pressed the arrow-up button.
        """
        if '\n' in self.text_before_cursor:
            lines = self.text_before_cursor.split('\n')
            current_line = lines[-1] # before the cursor
            previous_line = lines[-2]

            # When the current line is longer then the previous, move to the
            # last character of the previous line.
            if len(current_line) > len(previous_line):
                return self.cursor_position - len(current_line) - 1

            # Otherwise find the corresponding position in the previous line.
            else:
                return self.cursor_position - len(previous_line) - 1

    @property
    def cursor_down_position(self):
        """
        Return the cursor position (character index) where we would be if the
        user pressed the arrow-down button.
        """
        if '\n' in self.text_after_cursor:
            pos = len(self.text_before_cursor.split('\n')[-1])
            lines = self.text_after_cursor.split('\n')
            current_line = lines[0] # after the cursor
            next_line = lines[1]

            # When the current line is longer then the previous, move to the
            # last character of the next line.
            if pos > len(next_line):
                return self.cursor_position + len(current_line) + len(next_line) + 1

            # Otherwise find the corresponding position in the next line.
            else:
                return self.cursor_position + len(current_line) + pos + 1

    @property
    def cursor_at_the_end(self):
        """ True when the cursor is at the end of the text. """
        return self.cursor_position == len(self.text)

    @property
    def cursor_at_the_end_of_line(self):
        """ True when the cursor is at the end of this line. """
        return self.cursor_position_col == len(self.current_line)

    def has_match_at_current_position(self, sub):
        """
        `True` when this substring is found at the cursor position.
        """
        return self.text[self.cursor_position:].find(sub) == 0

    def find(self, sub, in_current_line=False, include_current_position=False):
        """
        Find `text` after the cursor, return position relative to the cursor
        position. Return `None` if nothing was found.
        """
        if in_current_line:
            text = self.current_line_after_cursor
        else:
            text = self.text_after_cursor

        if not include_current_position:
            text = text[1:]

        index = text.find(sub)

        if index >= 0:
            if not include_current_position:
                index += 1
            return index

    def find_all(self, sub):
        """
        Find all occurances of the substring. Return a list of absolute
        positions in the document.
        """
        return [a.start() for a in re.finditer(re.escape(sub), self.text)]

    def find_backwards(self, sub, in_current_line=False):
        """
        Find `text` before the cursor, return position relative to the cursor
        position. Return `None` if nothing was found.
        """
        if in_current_line:
            before_cursor = self.current_line_before_cursor
        else:
            before_cursor = self.text_before_cursor

        index = before_cursor.rfind(sub)

        if index >= 0:
            return index - len(before_cursor)

    def get_word_before_cursor(self):
        return self.text_before_cursor[self.find_start_of_previous_word():]

    def find_start_of_previous_word(self):
        """
        Return an index relative to the cursor position pointing to the start
        of the previous word. Return `None` if nothing was found.
        """
        # Reverse the text before the cursor, in order to do an efficient
        # backwards search.
        text_before_cursor = self.text_before_cursor[::-1]

        match = _FIND_WORD_RE.search(text_before_cursor)

        if match:
            return - match.end(1)

    def find_next_word_beginning(self):
        """
        Return an index relative to the cursor position pointing to the start
        of the next word. Return `None` if nothing was found.
        """
        iterable = _FIND_WORD_RE.finditer(self.text_after_cursor)

        try:
            # Take first match, unless it's the word on which we're right now.
            result = next(iterable).start(1)

            if result > 0:
                return result
            else:
                return next(iterable).start(1)

        except StopIteration:
            pass

    def find_next_word_ending(self, include_current_position=False):
        """
        Return an index relative to the cursor position pointing to the end
        of the next word. Return `None` if nothing was found.
        """
        if include_current_position:
            text = self.text_after_cursor
        else:
            text = self.text_after_cursor[1:]

        iterable = _FIND_WORD_RE.finditer(text)

        try:
            value = next(iterable).end(1)

            if include_current_position:
                return value
            else:
                return value + 1

        except StopIteration:
            pass

    def find_next_matching_line(self, match_func): # TODO: unittest.
        """
        Look downwards for empty lines.
        Return the line index, relative to the current line.
        """
        for index, line in enumerate(self.lines[self.cursor_position_row + 1:]):
            if match_func(line):
                return 1 + index

    def find_previous_matching_line(self, match_func): # TODO: unittest.
        """
        Look upwards for empty lines.
        Return the line index, relative to the current line.
        """
        for index, line in enumerate(self.lines[:self.cursor_position_row][::-1]):
            if match_func(line):
                return -1 - index
