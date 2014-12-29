"""
User interface Controls for the layout.
"""
from __future__ import unicode_literals
from pygments.token import Token

from six import with_metaclass
from abc import ABCMeta, abstractmethod

from prompt_toolkit.filters import AlwaysOff, Filter
from .processors import Processor
from .screen import Screen, Char, Point
from .utils import token_list_width

__all__ = (
    'TokenListControl',
    'FillControl',
    'BufferControl',
)


class UIControl(with_metaclass(ABCMeta, object)):
    """
    Base class for all user interface controls.
    """
    def reset(self):
        # Default reset. (Doesn't have to be implemented.)
        pass

    def preferred_width(self, cli):
        return None

    def preferred_height(self, cli, width):
        return None

    def has_focus(self, cli):
        return False

    @abstractmethod
    def create_screen(self, cli, width, height):
        """
        Write the content at this position to the screen.
        """
        pass


class _SimpleLRUCache(object):
    """
    Very simple LRU cache.

    :param maxsize: Maximum size of the cache. (Don't make it too big.)
    """
    def __init__(self, maxsize=8):
        self.maxsize = maxsize
        self._cache = []  # List of (key, value).

    def get(self, key, getter_func):
        """
        Get object from the cache.
        If not found, call `getter_func` to resolve it, and put that on the top
        of the cache instead.
        """
        # Look in cache first.
        for k, v in self._cache:
            if k == key:
                return v

        # Not found? Get it.
        value = getter_func()
        self._cache.append((key, value))

        if len(self._cache) > self.maxsize:
            self._cache = self._cache[-self.maxsize:]

        return value


class TokenListControl(UIControl):
    def __init__(self, get_tokens, default_char=None, align_right=False):
        assert default_char is None or isinstance(default_char, Char)
        self.get_tokens = get_tokens
        self.default_char = default_char
        self.align_right = align_right

    def __repr__(self):
        return 'TokenListControl(%r)' % self.get_tokens

    def preferred_width(self, cli):
        return token_list_width(self.get_tokens(cli))

    def preferred_height(self, cli, width):
        screen = self.create_screen(cli, width, None)
        return screen.current_height

    def create_screen(self, cli, width, height):
        screen = Screen(width, self.default_char)

        # Get tokens
        tokens = self.get_tokens(cli)

        # Align right
        if self.align_right:
            used_width = token_list_width(tokens)
            available_width = width - used_width
            tokens = [(self.default_char.token, ' ' * available_width)] + tokens

        screen.write_at_position(tokens, width)
        return screen

    @classmethod
    def static(cls, tokens):
        def get_static_tokens(cli):
            return tokens
        return cls(get_static_tokens)


class FillControl(UIControl):
    """
    Fill whole control with characters with this token.
    (Also helpful for debugging.)
    """
    def __init__(self, character=' ', token=Token):
        self.token = token
        self.character = character

    def __repr__(self):
        return 'FillControl(character=%r, token=%r)' % (self.character, self.token)

    def reset(self):
        pass

    def has_focus(self, cli):
        return False

    def create_screen(self, cli, width, height):
        char = Char(self.character, self.token)
        screen = Screen(width, char)
        screen.current_height = height
        return screen


class BufferControl(UIControl):
    def __init__(self,
                 input_processors=None,
                 lexer=None,
                 show_line_numbers=AlwaysOff(),
                 buffer_name='default',
                 default_token=Token,
                 menu_position=None):
        assert input_processors is None or all(isinstance(i, Processor) for i in input_processors)
        assert isinstance(show_line_numbers, Filter)
        assert menu_position is None or callable(menu_position)

        self.input_processors = input_processors or []
        self.show_line_numbers = show_line_numbers
        self.buffer_name = buffer_name
        self.default_token = default_token
        self.menu_position = menu_position

        if lexer:
            self.lexer = lexer(
                stripnl=False,
                stripall=False,
                ensurenl=False)
        else:
            self.lexer = None

        #: LRU cache for the lexer.
        #: Often, due to cursor movement, undo/redo and window resizing
        #: operations, it happens that a short time, the same document has to be
        #: lexed. This is a faily easy way to cache such an expensive operation.
        self._token_lru_cache = _SimpleLRUCache(maxsize=8)

        #: Keep a similar cache for rendered screens. (when we scroll up/down
        #: through the screen, or when we change another buffer, we don't want
        #: to recreate the same screen again.)
        self._screen_lru_cache = _SimpleLRUCache(maxsize=8)

    def _buffer(self, cli):
        """
        The buffer object that contains the 'main' content.
        """
        return cli.buffers[self.buffer_name]

    def has_focus(self, cli):
        return cli.focus_stack.current == self.buffer_name

    def preferred_width(self, cli):
        # Return the length of the longest line.
        return max(map(len, self._buffer(cli).document.lines))

    def preferred_height(self, cli, width):
        # Draw content on a screen using this width. Measure the height of the
        # result.
        screen = self.create_screen(cli, width, None)
        return screen.current_height

    def _get_input_tokens(self, cli, buffer):
        """
        Tokenize input text for highlighting.
        Return (tokens, cursor_transform_functions) tuple.
        """
        def get():
            if self.lexer:
                tokens = list(self.lexer.get_tokens(buffer.text))
            else:
                tokens = [(self.default_token, buffer.text)]

            # Run all processors over the input.
            # (They can transform both the tokens and the cursor position.)
            cursor_transform_functions = []

            for p in self.input_processors:
                tokens, f = p.run(cli, buffer, tokens)
                cursor_transform_functions.append(f)

            return tokens, cursor_transform_functions

        key = (
            buffer.text,

            # When the search state changes, highlighting will be different.
            # TODO: maybe use a `Processor` for the highlighting!
            buffer.isearch_state,
            buffer.isearch_state and buffer.isearch_state.isearch_text,

            # Include invalidation_hashes from all processors.
            tuple(p.invalidation_hash(cli, buffer) for p in self.input_processors),
        )

        return self._token_lru_cache.get(key, get)

    def _get_highlighted_characters(self, buffer):
        """
        Return a dictionary that maps the index of input string characters to
        their Token in case of highlighting.
        """
        highlighted_characters = {}

        # In case of incremental search, highlight all matches.
        if buffer.isearch_state:
            for index in buffer.document.find_all(buffer.isearch_state.isearch_text):
                if index == buffer.cursor_position:
                    token = Token.SearchMatch.Current
                else:
                    token = Token.SearchMatch

                highlighted_characters.update(dict([
                    (x, token) for x in range(index, index + len(buffer.isearch_state.isearch_text))
                ]))

        # In case of selection, highlight all matches.
        selection_range = buffer.document.selection_range()
        if selection_range:
            from_, to = selection_range

            for i in range(from_, to):
                highlighted_characters[i] = Token.SelectedText

        return highlighted_characters

    def _margin(self, cli, buffer):
        """
        Return a function that fills in the margin.
        """
        decimals = max(3, len('%s' % buffer.document.line_count))

        def numberred_margin(line_number):
            if line_number is not None:
                return [(Token.LineNumber, u'%%%si ' % decimals % (line_number + 1))]
            else:
                return [(Token.LineNumber, ' ' * (decimals + 1))]

        def no_margin(line_number):
            return []

        if self.show_line_numbers(cli):
            return numberred_margin
        else:
            return no_margin

    def create_screen(self, cli, width, height):
        buffer = self._buffer(cli)

        def _create_screen():
            screen = Screen(width)

            # Get tokens
            # Note: we add the space character at the end, because that's where
            #       the cursor can also be.
            input_tokens, cursor_transform_functions = self._get_input_tokens(cli, buffer)
            input_tokens += [(Token, ' ')]

            # 'Explode' tokens in characters.
            input_tokens = [(token, c) for token, text in input_tokens for c in text]

            # Apply highlighting.
            # XXX: not correct -> should go before input transforms!!!
            if not (cli.is_exiting or cli.is_aborting or cli.is_returning):
                highlighted_characters = self._get_highlighted_characters(buffer)

                for index, token in highlighted_characters.items():
                    input_tokens[index] = (token, input_tokens[index][1])

            indexes_to_pos = screen.write_at_position(
                input_tokens,
                screen.width,
                margin=self._margin(cli, buffer))

            def cursor_position_to_xy(cursor_position):
                # First get the real token position by applying all
                # transformations from the input processors.
                for f in cursor_transform_functions:
                    cursor_position = f(cursor_position)

                # Then look up into the table.
                try:
                    return indexes_to_pos[cursor_position]
                except KeyError:
                    # This can fail with KeyError, but only if one of the
                    # processors is returning invalid key locations.
                    raise
                    # return 0, 0

            return screen, cursor_position_to_xy

        # Build a key for the caching. If any of these parameters changes, we
        # have to recreate a new screen.
        key = (
            # When the text changes, we obviously have to recreate a new screen.
            buffer.text,

            # When the width changes, line wrapping will be different.
            # TODO: allow to disable line wrapping. + in that case, remove 'width'
            width,

            # When line numbers are enabled/disabled.
            self.show_line_numbers(cli),

            # When the search state changes, highlighting will be different.
            # TODO: maybe use a `Processor` for the highlighting!
            buffer.isearch_state,
            buffer.isearch_state and buffer.isearch_state.isearch_text,

            # When the selection changes, and the selection is highlighted.
            buffer.document.selection_range(),  # XXX: also use a processor for that one.

            # Include invalidation_hashes from all processors.
            tuple(p.invalidation_hash(cli, buffer) for p in self.input_processors),
        )

        # Get from cache, or create if this doesn't exist yet.
        screen, cursor_position_to_xy = self._screen_lru_cache.get(key, _create_screen)

        x, y = cursor_position_to_xy(buffer.cursor_position)
        screen.cursor_position = Point(y=y, x=x)

        # If there is an auto completion going on, use that start point for a
        # pop-up menu position. (But only when this buffer has the focus --
        # there is only one place for a menu, determined by the focussed buffer.)
        if cli.current_buffer_name == self.buffer_name:
            menu_position = self.menu_position(cli) if self.menu_position else None
            if menu_position is not None:
                assert isinstance(menu_position, int)
                x, y = cursor_position_to_xy(menu_position)
                screen.menu_position = Point(y=y, x=x)
            elif buffer.complete_state:
                x, y = cursor_position_to_xy(buffer.complete_state.original_document.cursor_position)
                screen.menu_position = Point(y=y, x=x)
            else:
                screen.menu_position = None

        return screen
