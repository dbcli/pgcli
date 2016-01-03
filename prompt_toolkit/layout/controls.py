"""
User interface Controls for the layout.
"""
from __future__ import unicode_literals
from pygments.token import Token

from abc import ABCMeta, abstractmethod
from collections import defaultdict, namedtuple
from six import with_metaclass

from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER
from prompt_toolkit.filters import to_cli_filter
from prompt_toolkit.mouse_events import MouseEventTypes
from prompt_toolkit.search_state import SearchState
from prompt_toolkit.selection import SelectionType
from prompt_toolkit.utils import get_cwidth, SimpleLRUCache

from .highlighters import Highlighter
from .lexers import Lexer, SimpleLexer
from .processors import Processor, Transformation
from .screen import Screen, Char, Point
from .utils import token_list_width, split_lines

import time

__all__ = (
    'BufferControl',
    'FillControl',
    'TokenListControl',
    'UIControl',
)


class UIControl(with_metaclass(ABCMeta, object)):
    """
    Base class for all user interface controls.
    """
    def reset(self):
        # Default reset. (Doesn't have to be implemented.)
        pass

    def preferred_width(self, cli, max_available_width):
        return None

    def preferred_height(self, cli, width):
        return None

    def has_focus(self, cli):
        """
        Return ``True`` when this user control has the focus.

        If so, the cursor will be displayed according to the cursor position
        reported in :meth:`.UIControl.create_screen`. If the created screen has
        the property ``show_cursor=False``, the cursor will be hidden from the
        output.
        """
        return False

    @abstractmethod
    def create_screen(self, cli, width, height):
        """
        Write the content at this position to the screen.

        Returns a :class:`.Screen` instance.

        Optionally, this can also return a (screen, highlighting) tuple, where
        the `highlighting` is a dictionary of dictionaries. Mapping
        y->x->Token if this position needs to be highlighted with that Token.
        """

    def mouse_handler(self, cli, mouse_event):
        """
        Handle mouse events.

        When `NotImplemented` is returned, it means that the given event is not
        handled by the `UIControl` itself. The `Window` or key bindings can
        decide to handle this event as scrolling or changing focus.

        :param cli: `CommandLineInterface` instance.
        :param mouse_event: `MouseEvent` instance.
        """
        return NotImplemented

    def move_cursor_down(self, cli):
        """
        Request to move the cursor down.
        This happens when scrolling down and the cursor is completely at the
        top.
        """

    def move_cursor_up(self, cli):
        """
        Request to move the cursor up.
        """


class TokenListControl(UIControl):
    """
    Control that displays a list of (Token, text) tuples.
    (It's mostly optimized for rather small widgets, like toolbars, menus, etc...)

    Mouse support:

        The list of tokens can also contain tuples of three items, looking like:
        (Token, text, handler). When mouse support is enabled and the user
        clicks on this token, then the given handler is called. That handler
        should accept two inputs: (CommandLineInterface, MouseEvent) and it
        should either handle the event or return `NotImplemented` in case we
        want the containing Window to handle this event.

    :param get_tokens: Callable that takes a `CommandLineInterface` instance
        and returns the list of (Token, text) tuples to be displayed right now.
    :param default_char: default :class:`.Char` (character and Token) to use
        for the background when there is more space available than `get_tokens`
        returns.
    :param get_default_char: Like `default_char`, but this is a callable that
        takes a :class:`prompt_toolkit.interface.CommandLineInterface` and
        returns a :class:`.Char` instance.
    :param has_focus: `bool` or `CLIFilter`, when this evaluates to `True`,
        this UI control will take the focus. The cursor will be shown in the
        upper left corner of this control, unless `get_token` returns a
        ``Token.SetCursorPosition`` token somewhere in the token list, then the
        cursor will be shown there.
    :param wrap_lines: `bool` or `CLIFilter`: Wrap long lines.
    """
    def __init__(self, get_tokens, default_char=None, get_default_char=None,
                 align_right=False, align_center=False,
                 has_focus=False, wrap_lines=True):
        assert default_char is None or isinstance(default_char, Char)
        assert get_default_char is None or callable(get_default_char)
        assert not (default_char and get_default_char)

        self.align_right = to_cli_filter(align_right)
        self.align_center = to_cli_filter(align_center)
        self._has_focus_filter = to_cli_filter(has_focus)
        self.wrap_lines = to_cli_filter(wrap_lines)

        self.get_tokens = get_tokens

        # Construct `get_default_char` callable.
        if default_char:
            get_default_char = lambda _: default_char
        elif not get_default_char:
            get_default_char = lambda _: Char(' ', Token)

        self.get_default_char = get_default_char

        #: Cache for rendered screens.
        self._screen_lru_cache = SimpleLRUCache(maxsize=18)
        self._token_lru_cache = SimpleLRUCache(maxsize=1)
            # Only cache one token list. We don't need the previous item.

        # Render info for the mouse support.
        self._tokens = None  # The last rendered tokens.
        self._pos_to_indexes = None  # Mapping from mouse positions (x,y) to
                                     # positions in the token list.

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.get_tokens)

    def _get_tokens_cached(self, cli):
        """
        Get tokens, but only retrieve tokens once during one render run.
        (This function is called several times during one rendering, because
        we also need those for calculating the dimensions.)
        """
        return self._token_lru_cache.get(
            cli.render_counter, lambda: self.get_tokens(cli))

    def has_focus(self, cli):
        return self._has_focus_filter(cli)

    def preferred_width(self, cli, max_available_width):
        """
        Return the preferred width for this control.
        That is the width of the longest line.
        """
        text = ''.join(t[1] for t in self._get_tokens_cached(cli))
        line_lengths = [get_cwidth(l) for l in text.split('\n')]
        return max(line_lengths)

    def preferred_height(self, cli, width):
        screen = self.create_screen(cli, width, None)
        return screen.height

    def create_screen(self, cli, width, height):
        # Get tokens
        tokens_with_mouse_handlers = self._get_tokens_cached(cli)

        default_char = self.get_default_char(cli)

        # Wrap/align right/center parameters.
        wrap_lines = self.wrap_lines(cli)
        right = self.align_right(cli)
        center = self.align_center(cli)

        def process_line(line):
            " Center or right align a single line. "
            used_width = token_list_width(line)
            padding = width - used_width
            if center:
                padding = int(padding / 2)
            return [(default_char.token, default_char.char * padding)] + line + [(Token, '\n')]

        if right or center:
            tokens2 = []
            for line in split_lines(tokens_with_mouse_handlers):
                tokens2.extend(process_line(line))
            tokens_with_mouse_handlers = tokens2

        # Strip mouse handlers from tokens.
        tokens = [tuple(item[:2]) for item in tokens_with_mouse_handlers]

        # Create screen, or take it from the cache.
        key = (default_char, tokens_with_mouse_handlers, width, wrap_lines, right, center)
        params = (default_char, tokens, width, wrap_lines, right, center)
        screen, self._pos_to_indexes = self._screen_lru_cache.get(key, lambda: self._get_screen(*params))

        self._tokens = tokens_with_mouse_handlers
        return screen

    @classmethod
    def _get_screen(cls, default_char, tokens, width, wrap_lines, right, center):
        screen = Screen(default_char, initial_width=width)

        # Only call write_data when we actually have tokens.
        # (Otherwise the screen height will go up from 0 to 1 while we don't
        # want that. -- An empty control should not take up any space.)
        if tokens:
            write_data_result = screen.write_data(tokens, width=(width if wrap_lines else None))

            indexes_to_pos = write_data_result.indexes_to_pos
            pos_to_indexes = dict((v, k) for k, v in indexes_to_pos.items())
        else:
            pos_to_indexes = {}

        return screen, pos_to_indexes

    @classmethod
    def static(cls, tokens):
        def get_static_tokens(cli):
            return tokens
        return cls(get_static_tokens)

    def mouse_handler(self, cli, mouse_event):
        """
        Handle mouse events.

        (When the token list contained mouse handlers and the user clicked on
        on any of these, the matching handler is called. This handler can still
        return `NotImplemented` in case we want the `Window` to handle this
        particular event.)
        """
        if self._pos_to_indexes:
            # Find position in the token list.
            position = mouse_event.position
            index = self._pos_to_indexes.get((position.x, position.y))

            if index is not None:
                # Find mouse handler for this character.
                count = 0
                for item in self._tokens:
                    count += len(item[1])
                    if count >= index:
                        if len(item) >= 3:
                            # Handler found. Call it.
                            handler = item[2]
                            handler(cli, mouse_event)
                            return
                        else:
                            break

        # Otherwise, don't handle here.
        return NotImplemented


class FillControl(UIControl):
    """
    Fill whole control with characters with this token.
    (Also helpful for debugging.)
    """
    def __init__(self, character=' ', token=Token):
        self.token = token
        self.character = character

    def __repr__(self):
        return '%s(character=%r, token=%r)' % (
            self.__class__.__name__, self.character, self.token)

    def reset(self):
        pass

    def has_focus(self, cli):
        return False

    def create_screen(self, cli, width, height):
        char = Char(self.character, self.token)
        screen = Screen(char, initial_width=width)
        return screen


class BufferControl(UIControl):
    """
    Control for visualising the content of a `Buffer`.

    :param input_processors: list of :class:`~prompt_toolkit.layout.processors.Processor`.
    :param lexer: :class:`~prompt_toolkit.layout.lexers.Lexer` instance for syntax highlighting.
    :param preview_search: `bool` or `CLIFilter`: Show search while typing.
    :param get_search_state: Callable that takes a CommandLineInterface and
        returns the SearchState to be used. (If not CommandLineInterface.search_state.)
    :param wrap_lines: `bool` or `CLIFilter`: Wrap long lines.
    :param buffer_name: String representing the name of the buffer to display.
    :param default_char: :class:`.Char` instance to use to fill the background. This is
        transparent by default.
    :param focus_on_click: Focus this buffer when it's click, but not yet focussed.
    """
    def __init__(self,
                 buffer_name=DEFAULT_BUFFER,
                 input_processors=None,
                 highlighters=None,
                 lexer=None,
                 preview_search=False,
                 search_buffer_name=SEARCH_BUFFER,
                 get_search_state=None,
                 wrap_lines=True,
                 menu_position=None,
                 default_char=None,
                 focus_on_click=False):
        assert input_processors is None or all(isinstance(i, Processor) for i in input_processors)
        assert highlighters is None or all(isinstance(i, Highlighter) for i in highlighters)
        assert menu_position is None or callable(menu_position)
        assert lexer is None or isinstance(lexer, Lexer)
        assert get_search_state is None or callable(get_search_state)

        self.preview_search = to_cli_filter(preview_search)
        self.get_search_state = get_search_state
        self.wrap_lines = to_cli_filter(wrap_lines)
        self.focus_on_click = to_cli_filter(focus_on_click)

        self.input_processors = input_processors or []
        self.highlighters = highlighters or []
        self.buffer_name = buffer_name
        self.menu_position = menu_position
        self.lexer = lexer or SimpleLexer()
        self.default_char = default_char or Char(token=Token.Transparent)
        self.search_buffer_name = search_buffer_name

        #: LRU cache for the lexer.
        #: Often, due to cursor movement, undo/redo and window resizing
        #: operations, it happens that a short time, the same document has to be
        #: lexed. This is a faily easy way to cache such an expensive operation.
        self._token_lru_cache = SimpleLRUCache(maxsize=8)

        #: Keep a similar cache for rendered screens. (when we scroll up/down
        #: through the screen, or when we change another buffer, we don't want
        #: to recreate the same screen again.)
        self._screen_lru_cache = SimpleLRUCache(maxsize=8)

        #: Highlight Cache.
        #: When nothing of the buffer content or processors has changed, but
        #: the highlighting of the selection/search changes,
        self._highlight_lru_cache = SimpleLRUCache(maxsize=8)

        self._xy_to_cursor_position = None
        self._last_click_timestamp = None

    def _buffer(self, cli):
        """
        The buffer object that contains the 'main' content.
        """
        return cli.buffers[self.buffer_name]

    def has_focus(self, cli):
        # This control gets the focussed if the actual `Buffer` instance has the
        # focus or when any of the `InputProcessor` classes tells us that it
        # wants the focus. (E.g. in case of a reverse-search, where the actual
        # search buffer may not be displayed, but the "reverse-i-search" text
        # should get the focus.)
        return cli.current_buffer_name == self.buffer_name or \
            any(i.has_focus(cli) for i in self.input_processors)

    def preferred_width(self, cli, max_available_width):
        # Return the length of the longest line.
        return max(map(len, self._buffer(cli).document.lines))

    def preferred_height(self, cli, width):
        # Draw content on a screen using this width. Measure the height of the
        # result.
        screen, highlighters = self.create_screen(cli, width, None)
        return screen.height

    def _get_input_tokens(self, cli, document):
        """
        Tokenize input text for highlighting.
        Return (tokens, source_to_display, display_to_source) tuple.

        :param document: The document to be shown. This can be `buffer.document`
                         but could as well be a different one, in case we are
                         searching through the history. (Buffer.document_for_search)
        """
        def get():
            # Call lexer.
            tokens = list(self.lexer.get_tokens(cli, document.text))

            # 'Explode' tokens in characters.
            # (Some input processors -- like search/selection highlighter --
            # rely on that each item in the tokens array only contains one
            # character.)
            tokens = [(token, c) for token, text in tokens for c in text]

            # Run all processors over the input.
            # (They can transform both the tokens and the cursor position.)
            source_to_display_functions = []
            display_to_source_functions = []

            d_ = document  # Each processor receives the document of the previous one.

            for p in self.input_processors:
                transformation  = p.apply_transformation(cli, d_, tokens)
                d_ = transformation.document
                assert isinstance(transformation, Transformation)

                tokens = transformation.tokens
                source_to_display_functions.append(transformation.source_to_display)
                display_to_source_functions.append(transformation.display_to_source)

            # Chain cursor transformation (movement) functions.

            def source_to_display(cursor_position):
                " Chained source_to_display. "
                for f in source_to_display_functions:
                    cursor_position = f(cursor_position)
                return cursor_position

            def display_to_source(cursor_position):
                " Chained display_to_source. "
                for f in reversed(display_to_source_functions):
                    cursor_position = f(cursor_position)
                return cursor_position

            return tokens, source_to_display, display_to_source

        key = (
            document.text,

            # Include invalidation_hashes from all processors.
            tuple(p.invalidation_hash(cli, document) for p in self.input_processors),
        )

        return self._token_lru_cache.get(key, get)

    def create_screen(self, cli, width, height):
        buffer = self._buffer(cli)

        # Get the document to be shown. If we are currently searching (the
        # search buffer has focus, and the preview_search filter is enabled),
        # then use the search document, which has possibly a different
        # text/cursor position.)
        def preview_now():
            """ True when we should preview a search. """
            return bool(self.preview_search(cli) and
                        cli.buffers[self.search_buffer_name].text)

        if preview_now():
            if self.get_search_state:
                ss = self.get_search_state(cli)
            else:
                ss = cli.search_state

            document = buffer.document_for_search(SearchState(
                text=cli.current_buffer.text,
                direction=ss.direction,
                ignore_case=ss.ignore_case))
        else:
            document = buffer.document

        # Wrap.
        wrap_width = width if self.wrap_lines(cli) else None

        def _create_screen():
            screen = Screen(self.default_char, initial_width=width)

            # Get tokens
            # Note: we add the space character at the end, because that's where
            #       the cursor can also be.
            input_tokens, source_to_display, display_to_source = self._get_input_tokens(cli, document)
            input_tokens += [(self.default_char.token, ' ')]

            write_data_result = screen.write_data(input_tokens, width=wrap_width)
            indexes_to_pos = write_data_result.indexes_to_pos
            line_lengths = write_data_result.line_lengths

            pos_to_indexes = dict((v, k) for k, v in indexes_to_pos.items())

            def cursor_position_to_xy(cursor_position):
                """ Turn a cursor position in the buffer into x/y coordinates
                on the screen. """
                cursor_position = min(len(document.text), cursor_position)

                # First get the real token position by applying all transformations.
                cursor_position = source_to_display(cursor_position)

                # Then look up into the table.
                try:
                    return indexes_to_pos[cursor_position]
                except KeyError:
                    # This can fail with KeyError, but only if one of the
                    # processors is returning invalid key locations.
                    raise
                    # return 0, 0

            def xy_to_cursor_position(x, y):
                """ Turn x/y screen coordinates back to the original cursor
                position in the buffer. """
                # Look up reverse in table.
                while x > 0 or y > 0:
                    try:
                        index = pos_to_indexes[x, y]
                        break
                    except KeyError:
                        # No match found -> mouse click outside of region
                        # containing text. Look to the left or up.
                        if x: x -= 1
                        elif y: y -=1
                else:
                    # Nobreak.
                    index = 0

                # Transform.
                return display_to_source(index)

            return screen, cursor_position_to_xy, xy_to_cursor_position, line_lengths

        # Build a key for the caching. If any of these parameters changes, we
        # have to recreate a new screen.
        key = (
            # When the text changes, we obviously have to recreate a new screen.
            document.text,

            # When the width changes, line wrapping will be different.
            # (None when disabled.)
            wrap_width,

            # Include invalidation_hashes from all processors.
            tuple(p.invalidation_hash(cli, document) for p in self.input_processors),
        )

        # Get from cache, or create if this doesn't exist yet.
        screen, cursor_position_to_xy, self._xy_to_cursor_position, line_lengths = \
            self._screen_lru_cache.get(key, _create_screen)

        x, y = cursor_position_to_xy(document.cursor_position)
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
                # Position for completion menu.
                # Note: We use 'min', because the original cursor position could be
                #       behind the input string when the actual completion is for
                #       some reason shorter than the text we had before. (A completion
                #       can change and shorten the input.)
                x, y = cursor_position_to_xy(
                    min(buffer.cursor_position,
                        buffer.complete_state.original_document.cursor_position))
                screen.menu_position = Point(y=y, x=x)
            else:
                screen.menu_position = None

        # Add highlighting.
        highlight_key = (
            key,  # Includes everything from the 'key' above. (E.g. when the
                     # document changes, we have to recalculate highlighting.)

            # Include invalidation_hashes from all highlighters.
            tuple(h.invalidation_hash(cli, document) for h in self.highlighters)
        )

        highlighting = self._highlight_lru_cache.get(highlight_key, lambda:
            self._get_highlighting(cli, document, cursor_position_to_xy, line_lengths))

        return screen, highlighting

    def _get_highlighting(self, cli, document, cursor_position_to_xy, line_lengths):
        """
        Return a _HighlightDict for the highlighting. (This is a lazy dict of dicts.)

        The Window class will apply this for the visible regions. - That way,
        we don't have to recalculate the screen again for each selection/search
        change.

        :param line_lengths: Maps line numbers to the length of these lines.
        """
        def get_row_size(y):
            " Return the max 'x' value for a given row in the screen. "
            return max(1, line_lengths.get(y, 0))

        # Get list of fragments.
        row_to_fragments = defaultdict(list)

        for h in self.highlighters:
            for fragment in h.get_fragments(cli, document):
                # Expand fragments.
                start_column, start_row = cursor_position_to_xy(fragment.start)
                end_column, end_row = cursor_position_to_xy(fragment.end)
                token = fragment.token

                if start_row == end_row:
                    # Single line highlighting.
                    row_to_fragments[start_row].append(
                        _HighlightFragment(start_column, end_column, token))
                else:
                    # Multi line highlighting.
                    # (First line.)
                    row_to_fragments[start_row].append(
                        _HighlightFragment(start_column, get_row_size(start_row), token))

                    # (Middle lines.)
                    for y in range(start_row + 1, end_row):
                        row_to_fragments[y].append(_HighlightFragment(0, get_row_size(y), token))

                    # (Last line.)
                    row_to_fragments[end_row].append(_HighlightFragment(0, end_column, token))

        # Create dict to return.
        return _HighlightDict(row_to_fragments)

    def mouse_handler(self, cli, mouse_event):
        """
        Mouse handler for this control.
        """
        buffer = self._buffer(cli)
        position = mouse_event.position

        # Focus buffer when clicked.
        if self.has_focus(cli):
            if self._xy_to_cursor_position:
                # Translate coordinates back to the cursor position of the
                # original input.
                pos = self._xy_to_cursor_position(position.x, position.y)

                # Set the cursor position.
                if pos <= len(buffer.text):
                    if mouse_event.event_type == MouseEventTypes.MOUSE_DOWN:
                        buffer.exit_selection()
                        buffer.cursor_position = pos

                    elif mouse_event.event_type == MouseEventTypes.MOUSE_UP:
                        # When the cursor was moved to another place, select the text.
                        # (The >1 is actually a small but acceptable workaround for
                        # selecting text in Vi navigation mode. In navigation mode,
                        # the cursor can never be after the text, so the cursor
                        # will be repositioned automatically.)
                        if abs(buffer.cursor_position - pos) > 1:
                            buffer.start_selection(selection_type=SelectionType.CHARACTERS)
                            buffer.cursor_position = pos

                        # Select word around cursor on double click.
                        # Two MOUSE_UP events in a short timespan are considered a double click.
                        double_click = self._last_click_timestamp and time.time() - self._last_click_timestamp < .3
                        self._last_click_timestamp = time.time()

                        if double_click:
                            start, end = buffer.document.find_boundaries_of_current_word()
                            buffer.cursor_position += start
                            buffer.start_selection(selection_type=SelectionType.CHARACTERS)
                            buffer.cursor_position += end - start
                    else:
                        # Don't handle scroll events here.
                        return NotImplemented

        # Not focussed, but focussing on click events.
        else:
            if self.focus_on_click(cli) and mouse_event.event_type == MouseEventTypes.MOUSE_UP:
                # Focus happens on mouseup. (If we did this on mousedown, the
                # up event will be received at the point where this widget is
                # focussed and be handled anyway.)
                cli.focus(self.buffer_name)
            else:
                return NotImplemented

    def move_cursor_down(self, cli):
        b = self._buffer(cli)
        b.cursor_position += b.document.get_cursor_down_position()

    def move_cursor_up(self, cli):
        b = self._buffer(cli)
        b.cursor_position += b.document.get_cursor_up_position()


_HighlightFragment = namedtuple('_HighlightFragment', 'start_column end_column token')  # End is excluded.


class _HighlightDict(dict):
    """
    Helper class to contain the highlighting.
    Maps 'y' coordinate to 'x' coordinate to Token.

    :param row_to_fragments: Dictionary that maps row numbers to list of `_HighlightFragment`.
    """
    def __init__(self, row_to_fragments):
        self.row_to_fragments = row_to_fragments

    def __missing__(self, key):
        result = _HighlightDictRow(self.row_to_fragments[key])
        self[key] = result
        return result

    def __repr__(self):
        return '_HighlightDict(%r)' % (dict.__repr__(self), )


class _HighlightDictRow(dict):
    def __init__(self, list_of_fragments):
        self.list_of_fragments = list_of_fragments

    def __missing__(self, key):
        result = None

        for f in self.list_of_fragments:
            if f.start_column <= key < f.end_column:  # End is excluded.
                result = f.token
                break

        self[key] = result
        return result
