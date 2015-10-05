"""
"""
from __future__ import unicode_literals

import re
import six
import string

from .selection import SelectionType, SelectionState

__all__ = ('Document',)


# Regex for finding "words" in documents. (We consider a group of alnum
# characters a word, but also a group of special characters a word, as long as
# it doesn't contain a space.)
# (This is a 'word' in Vi.)
_FIND_WORD_RE = re.compile(r'([a-zA-Z0-9_]+|[^a-zA-Z0-9_\s]+)')
_FIND_CURRENT_WORD_RE = re.compile(r'^([a-zA-Z0-9_]+|[^a-zA-Z0-9_\s]+)')
_FIND_CURRENT_WORD_INCLUDE_TRAILING_WHITESPACE_RE = re.compile(r'^(([a-zA-Z0-9_]+|[^a-zA-Z0-9_\s]+)\s*)')

# Regex for finding "WORDS" in documents.
# (This is a 'WORD in Vi.)
_FIND_BIG_WORD_RE = re.compile(r'([^\s]+)')
_FIND_CURRENT_BIG_WORD_RE = re.compile(r'^([^\s]+)')
_FIND_CURRENT_BIG_WORD_INCLUDE_TRAILING_WHITESPACE_RE = re.compile(r'^([^\s]+\s*)')


class Document(object):
    """
    This is a immutable class around the text and cursor position, and contains
    methods for querying this data, e.g. to give the text before the cursor.

    This class is usually instantiated by a :class:`~prompt_toolkit.buffer.Buffer`
    object, and accessed as the `document` property of that class.

    :param text: string
    :param cursor_position: int
    :param selection: :class:`SelectionState`
    """
    __slots__ = ('text', 'cursor_position', 'selection')

    def __init__(self, text='', cursor_position=None, selection=None):
        assert isinstance(text, six.text_type), 'Got %r' % text
        assert selection is None or isinstance(selection, SelectionState)

        # Check cursor position. It can also be right after the end. (Where we
        # insert text.)
        assert cursor_position is None or cursor_position <= len(text), AssertionError(
                'cursor_position=%r, len_text=%r' % (cursor_position, len(text)))

        # By default, if no cursor position was given, make sure to put the
        # cursor position is at the end of the document. This is what makes
        # sense in most places.
        if cursor_position is None:
            cursor_position = len(text)

        self.text = text
        self.cursor_position = cursor_position
        self.selection = selection

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.text, self.cursor_position)

    @property
    def current_char(self):
        """ Return character under cursor or an empty string. """
        return self._get_char_relative_to_cursor(0) or ''

    @property
    def char_before_cursor(self):
        """ Return character before the cursor or an empty string. """
        return self._get_char_relative_to_cursor(-1) or ''

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
        """
        Return character relative to cursor position, or empty string
        """
        try:
            return self.text[self.cursor_position + offset]
        except IndexError:
            return ''

    @property
    def on_first_line(self):
        """
        True when we are at the first line.
        """
        return self.cursor_position_row == 0

    @property
    def on_last_line(self):
        """
        True when we are at the last line.
        """
        return self.cursor_position_row == self.line_count - 1

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

    def translate_index_to_position(self, index):  # TODO: make this 0-based indexed!!!
        """
        Given an index for the text, return the corresponding (row, col) tuple.
        """
        text_before_position = self.text[:index]

        row = len(text_before_position.split('\n'))
        col = len(text_before_position.split('\n')[-1])

        return row, col

    def translate_row_col_to_index(self, row, col):
        """
        Given a (row, col) tuple, return the corresponding index.
        (Row and col params are 0-based.)
        """
        result = len('\n'.join(self.lines[:row])) + (len('\n') if row > 0 else 0) + col

        # Keep in range. (len(self.text) is included, because the cursor can be
        # right after the end of the text as well.)
        result = max(0, min(result, len(self.text)))
        return result

    @property
    def is_cursor_at_the_end(self):
        """ True when the cursor is at the end of the text. """
        return self.cursor_position == len(self.text)

    @property
    def is_cursor_at_the_end_of_line(self):
        """ True when the cursor is at the end of this line. """
        return self.cursor_position_col == len(self.current_line)

    def has_match_at_current_position(self, sub):
        """
        `True` when this substring is found at the cursor position.
        """
        return self.text[self.cursor_position:].find(sub) == 0

    def find(self, sub, in_current_line=False, include_current_position=False,
            ignore_case=False, count=1):
        """
        Find `text` after the cursor, return position relative to the cursor
        position. Return `None` if nothing was found.

        :param count: Find the n-th occurance.
        """
        assert isinstance(ignore_case, bool)

        if in_current_line:
            text = self.current_line_after_cursor
        else:
            text = self.text_after_cursor

        if not include_current_position:
            if len(text) == 0:
                return  # (Otherwise, we always get a match for the empty string.)
            else:
                text = text[1:]

        flags = re.IGNORECASE if ignore_case else 0
        iterator = re.finditer(re.escape(sub), text, flags)

        try:
            for i, match in enumerate(iterator):
                if i + 1 == count:
                    if include_current_position:
                        return match.start(0)
                    else:
                        return match.start(0) + 1
        except StopIteration:
            pass

    def find_all(self, sub, ignore_case=False):
        """
        Find all occurances of the substring. Return a list of absolute
        positions in the document.
        """
        flags = re.IGNORECASE if ignore_case else 0
        return [a.start() for a in re.finditer(re.escape(sub), self.text, flags)]

    def find_backwards(self, sub, in_current_line=False, ignore_case=False, count=1):
        """
        Find `text` before the cursor, return position relative to the cursor
        position. Return `None` if nothing was found.

        :param count: Find the n-th occurance.
        """
        if in_current_line:
            before_cursor = self.current_line_before_cursor[::-1]
        else:
            before_cursor = self.text_before_cursor[::-1]

        flags = re.IGNORECASE if ignore_case else 0
        iterator = re.finditer(re.escape(sub[::-1]), before_cursor, flags)

        try:
            for i, match in enumerate(iterator):
                if i + 1 == count:
                    return - match.start(0) - len(sub)
        except StopIteration:
            pass

    def get_word_before_cursor(self, WORD=False):
        """
        Give the word before the cursor.
        If we have whitespace before the cursor this returns an empty string.
        """
        if self.text_before_cursor[-1:].isspace():
            return ''
        else:
            return self.text_before_cursor[self.find_start_of_previous_word(WORD=WORD):]

    def find_start_of_previous_word(self, count=1, WORD=False):
        """
        Return an index relative to the cursor position pointing to the start
        of the previous word. Return `None` if nothing was found.
        """
        # Reverse the text before the cursor, in order to do an efficient
        # backwards search.
        text_before_cursor = self.text_before_cursor[::-1]

        regex = _FIND_BIG_WORD_RE if WORD else _FIND_WORD_RE
        iterator = regex.finditer(text_before_cursor)

        try:
            for i, match in enumerate(iterator):
                if i + 1 == count:
                    return - match.end(1)
        except StopIteration:
            pass

    def find_boundaries_of_current_word(self, WORD=False, include_leading_whitespace=False,
                                        include_trailing_whitespace=False):
        """
        Return the relative boundaries (startpos, endpos) of the current word under the
        cursor. (This is at the current line, because line boundaries obviously
        don't belong to any word.)
        If not on a word, this returns (0,0)
        """
        text_before_cursor = self.current_line_before_cursor[::-1]
        text_after_cursor = self.current_line_after_cursor

        def get_regex(include_whitespace):
            return {
                (False, False): _FIND_CURRENT_WORD_RE,
                (False, True): _FIND_CURRENT_WORD_INCLUDE_TRAILING_WHITESPACE_RE,
                (True, False): _FIND_CURRENT_BIG_WORD_RE,
                (True, True): _FIND_CURRENT_BIG_WORD_INCLUDE_TRAILING_WHITESPACE_RE,
            }[(WORD, include_whitespace)]

        match_before = get_regex(include_leading_whitespace).search(text_before_cursor)
        match_after = get_regex(include_trailing_whitespace).search(text_after_cursor)

        # When there is a match before and after, and we're not looking for
        # WORDs, make sure that both the part before and after the cursor are
        # either in the [a-zA-Z_] alphabet or not. Otherwise, drop the part
        # before the cursor.
        if not WORD and match_before and match_after:
            c1 = self.text[self.cursor_position - 1]
            c2 = self.text[self.cursor_position]
            alphabet = string.ascii_letters + '0123456789_'

            if (c1 in alphabet) != (c2 in alphabet):
                match_before = None

        return (
            - match_before.end(1) if match_before else 0,
            match_after.end(1) if match_after else 0
        )

    def get_word_under_cursor(self, WORD=False):
        """
        Return the word, currently below the cursor.
        This returns an empty string when the cursor is on a whitespace region.
        """
        start, end = self.find_boundaries_of_current_word(WORD=WORD)
        return self.text[self.cursor_position + start: self.cursor_position + end]

    def find_next_word_beginning(self, count=1, WORD=False):
        """
        Return an index relative to the cursor position pointing to the start
        of the next word. Return `None` if nothing was found.
        """
        regex = _FIND_BIG_WORD_RE if WORD else _FIND_WORD_RE
        iterator = regex.finditer(self.text_after_cursor)

        try:
            for i, match in enumerate(iterator):
                # Take first match, unless it's the word on which we're right now.
                if i == 0 and match.start(1) == 0:
                    count += 1

                if i + 1 == count:
                    return match.start(1)
        except StopIteration:
            pass

    def find_next_word_ending(self, include_current_position=False, count=1, WORD=False):
        """
        Return an index relative to the cursor position pointing to the end
        of the next word. Return `None` if nothing was found.
        """
        if include_current_position:
            text = self.text_after_cursor
        else:
            text = self.text_after_cursor[1:]

        regex = _FIND_BIG_WORD_RE if WORD else _FIND_WORD_RE
        iterable = regex.finditer(text)

        try:
            for i, match in enumerate(iterable):
                if i + 1 == count:
                    value = match.end(1)

                    if include_current_position:
                        return value
                    else:
                        return value + 1

        except StopIteration:
            pass

    def find_previous_word_beginning(self, count=1, WORD=False):
        """
        Return an index relative to the cursor position pointing to the start
        of the next word. Return `None` if nothing was found.
        """
        regex = _FIND_BIG_WORD_RE if WORD else _FIND_WORD_RE
        iterator = regex.finditer(self.text_before_cursor[::-1])

        try:
            for i, match in enumerate(iterator):
                if i + 1 == count:
                    return - match.end(1)
        except StopIteration:
            pass

    def find_next_matching_line(self, match_func, count=1):
        """
        Look downwards for empty lines.
        Return the line index, relative to the current line.
        """
        result = None

        for index, line in enumerate(self.lines[self.cursor_position_row + 1:]):
            if match_func(line):
                result = 1 + index
                count -= 1

            if count == 0:
                break

        return result

    def find_previous_matching_line(self, match_func, count=1):
        """
        Look upwards for empty lines.
        Return the line index, relative to the current line.
        """
        result = None

        for index, line in enumerate(self.lines[:self.cursor_position_row][::-1]):
            if match_func(line):
                result = -1 - index
                count -= 1

            if count == 0:
                break

        return result

    def get_cursor_left_position(self, count=1):
        """
        Relative position for cursor left.
        """
        return - min(self.cursor_position_col, count)

    def get_cursor_right_position(self, count=1):
        """
        Relative position for cursor_right.
        """
        return min(count, len(self.current_line_after_cursor))

    def get_cursor_up_position(self, count=1):
        """
        Return the relative cursor position (character index) where we would be if the
        user pressed the arrow-up button.
        """
        assert count >= 1

        count = min(self.text_before_cursor.count('\n'), count)

        if count:
            pos = self.cursor_position_col

            lines = self.text_before_cursor.split('\n')
            skip_lines = '\n'.join(lines[-count-1:])
            new_line = lines[-count-1]

            # When the current line is longer then the previous, move to the
            # last character of the previous line.
            if pos > len(new_line):
                return - len(skip_lines) + len(new_line)

            # Otherwise find the corresponding position in the previous line.
            else:
                return - len(skip_lines) + pos
        return 0

    def get_cursor_down_position(self, count=1):
        """
        Return the relative cursor position (character index) where we would be if the
        user pressed the arrow-down button.
        """
        assert count >= 1

        count = min(self.text_after_cursor.count('\n'), count)

        if count:
            pos = self.cursor_position_col

            lines = self.text_after_cursor.split('\n')
            skip_lines = '\n'.join(lines[:count])
            new_line = lines[count]

            # When the current line is longer then the previous, move to the
            # last character of the next line.
            if pos > len(new_line):
                return len(skip_lines) + len(new_line) + 1

            # Otherwise find the corresponding position in the next line.
            else:
                return len(skip_lines) + pos + 1

        return 0

    @property
    def matching_bracket_position(self):
        """
        Return relative cursor position of matching [, (, { or < bracket.
        """
        stack = 1

        for A, B in '()', '[]', '{}', '<>':
            if self.current_char == A:
                for i, c in enumerate(self.text_after_cursor[1:]):
                    if c == A:
                        stack += 1
                    elif c == B:
                        stack -= 1

                    if stack == 0:
                        return i + 1

            elif self.current_char == B:
                for i, c in enumerate(reversed(self.text_before_cursor)):
                    if c == B:
                        stack += 1
                    elif c == A:
                        stack -= 1

                    if stack == 0:
                        return - (i + 1)

        return 0

    def get_start_of_document_position(self):
        """ Relative position for the start of the document. """
        return - self.cursor_position

    def get_end_of_document_position(self):
        """ Relative position for the end of the document. """
        return len(self.text) - self.cursor_position

    def get_start_of_line_position(self, after_whitespace=False):
        """ Relative position for the start of this line. """
        if after_whitespace:
            current_line = self.current_line
            return len(current_line) - len(current_line.lstrip()) - self.cursor_position_col
        else:
            return - len(self.current_line_before_cursor)

    def get_end_of_line_position(self):
        """ Relative position for the end of this line. """
        return len(self.current_line_after_cursor)

    def last_non_blank_of_current_line_position(self):
        """
        Relative position for the last non blank character of this line.
        """
        return len(self.current_line_after_cursor.rstrip())

    def get_column_cursor_position(self, column):
        """
        Return the relative cursor position for this column at the current
        line. (It will stay between the boundaries of the line in case of a
        larger number.)
        """
        line_length = len(self.current_line)
        current_column = self.cursor_position_col
        column = max(0, min(line_length, column))

        return column - current_column

    def selection_range(self):
        """
        Return (from, to) tuple of the selection or `None` if nothing was selected.
        start and end position are always included in the selection.
        """
        if self.selection:
            from_, to = sorted([self.cursor_position, self.selection.original_cursor_position])

            # In case of a LINES selection, go to the start/end of the lines.
            if self.selection.type == SelectionType.LINES:
                from_ = max(0, self.text[:from_].rfind('\n') + 1)

                if self.text[to:].find('\n') >= 0:
                    to += self.text[to:].find('\n')
                else:
                    to = len(self.text)

            return from_, to

    def empty_line_count_at_the_end(self):
        """
        Return number of empty lines at the end of the document.
        """
        count = 0
        for line in self.lines[::-1]:
            if not line or line.isspace():
                count += 1
            else:
                break

        return count

    # Modifiers.

    def insert_after(self, text):
        """
        Create a new document, with this text inserted after the buffer.
        It keeps selection ranges and cursor position in sync.
        """
        return Document(
                text=self.text + text,
                cursor_position=self.cursor_position,
                selection=self.selection)

    def insert_before(self, text):
        """
        Create a new document, with this text inserted before the buffer.
        It keeps selection ranges and cursor position in sync.
        """
        selection_state = self.selection

        if selection_state:
            selection_state = SelectionState(
                original_cursor_position=selection_state.original_cursor_position + len(text),
                type=selection_state.type)

        return Document(
                text=text + self.text,
                cursor_position=self.cursor_position + len(text),
                selection=selection_state)
