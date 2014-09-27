"""
Layout representation.
"""
from __future__ import unicode_literals

from pygments.token import Token
from ..renderer import Screen, Size, Point, Char


__all__ = (
    'Layout',
)

class _SimpleLRUCache(object):
    """
    Very simple LRU cache.

    :param maxsize: Maximum size of the cache. (Don't make it too big.)
    """
    def __init__(self, maxsize=8):
        self.maxsize = maxsize
        self._cache = [] # List of (key, value).

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


class Layout(object):
    """
    Default prompt class.

    :param before_input: What to show before the actual input.
    :param input_processors: Processors for transforming the tokens received
                             from the `Code` object. (This can be used for
                             displaying password input as '*' or for
                             highlighting mismatches of brackets in case of
                             Python input.)
    :param menus: List of `Menu` classes or `None`.
    """
    def __init__(self,
            before_input=None,
            after_input=None,
            left_margin=None,
            top_toolbars=None,
            bottom_toolbars=None,
            input_processors=None,
            menus=None,
            lexer=None,
            min_height=0,
            show_tildes=False,
            line_name='default',
            ):

        self.before_input = before_input
        self.after_input = after_input
        self.left_margin = left_margin
        self.top_toolbars = top_toolbars or []
        self.bottom_toolbars = bottom_toolbars or []
        self.input_processors = input_processors or []
        self.menus = menus or []
        self.min_height = min_height
        self.show_tildes = show_tildes
        self.line_name = line_name

        if lexer:
            self.lexer = lexer(
                stripnl=False,
                stripall=False,
                ensurenl=False)
        else:
            self.lexer = None

        #: LRU cache for the lexer.
        #: Often, due to cursor movement and undo/redo operations, it happens that
        #: in a short time, the same document has to be lexed. This is a faily easy
        #: way to cache such an expensive operation.
        #: (Set to ``None`` to disable cache.)
        self._token_lru_cache = _SimpleLRUCache(maxsize=8)

        self.reset()

    def _line(self, cli):
        """
        The line object that contains the 'main' content.
        """
        return cli.lines[self.line_name]

    def reset(self):
        #: Vertical scrolling position of the main content.
        self.vertical_scroll = 0

    def get_input_tokens(self, cli):
        """
        Tokenize input text for highlighting.
        """
        line = self._line(cli)

        def get():
            if self.lexer:
                tokens = list(self.lexer.get_tokens(line.text))
            else:
                tokens = [(Token, line.text)]

            for p in self.input_processors:
                tokens = p.process_tokens(tokens)
            return tokens

        return self._token_lru_cache.get(line.text, get)

    def get_highlighted_characters(self, line):
        """
        Return a dictionary that maps the index of input string characters to
        their Token in case of highlighting.
        """
        highlighted_characters = {}

        # In case of incremental search, highlight all matches.
        if line.isearch_state:
            for index in line.document.find_all(line.isearch_state.isearch_text):
                if index == line.cursor_position:
                    token = Token.IncrementalSearchMatch.Current
                else:
                    token = Token.IncrementalSearchMatch

                highlighted_characters.update({
                    x: token for x in range(index, index + len(line.isearch_state.isearch_text))
                })

        # In case of selection, highlight all matches.
        selection_range = line.document.selection_range()
        if selection_range:
            from_, to = selection_range

            for i in range(from_, to):
                highlighted_characters[i] = Token.SelectedText

        return highlighted_characters

    def _write_input(self, cli, screen):
        # Get tokens
        # Note: we add the space character at the end, because that's where
        #       the cursor can also be.
        input_tokens = self.get_input_tokens(cli) + [(Token, ' ')]

        # 'Explode' tokens in characters.
        input_tokens = [(token, c) for token, text in input_tokens for c in text]

        # Apply highlighting.
        if not (cli.is_exiting or cli.is_aborting or cli.is_returning):
            highlighted_characters = self.get_highlighted_characters(self._line(cli))

            for index, token in highlighted_characters.items():
                input_tokens[index] = (token, input_tokens[index][1])

        for index, (token, c) in enumerate(input_tokens):
            # Insert char.
            screen.write_char(c, token,
                              string_index=index,
                              set_cursor_position=(index == self._line(cli).cursor_position))

    def write_input_scrolled(self, cli, screen, write_content,
                             min_height=1, top_margin=0, bottom_margin=0):
        """
        Write visible part of the input to the screen. (Scroll if the input is
        too large.)

        :return: Cursor row position after the scroll region.
        """
        is_done = cli.is_exiting or cli.is_aborting or cli.is_returning
        left_margin_width = self.left_margin.width(cli) if self.left_margin else 0

        # Make sure that `min_height` is in the 0..max_height interval.
        min_height = min(min_height, screen.size.rows)
        min_height = max(0, min_height)
        min_height -= (top_margin+ bottom_margin)

        # Write to a temp screen first. (Later, we will copy the visible region
        # of this screen to the real screen.)
        temp_screen = Screen(Size(columns=screen.size.columns - left_margin_width,
                                  rows=screen.size.rows))
        write_content(temp_screen)

        # Determine the maximum height.
        max_height = screen.size.rows - bottom_margin - top_margin

        # Scroll.
        if True:
            # Scroll back if we scrolled to much and there's still space at the top.
            if self.vertical_scroll > temp_screen.current_height - max_height:
                self.vertical_scroll = max(0, temp_screen.current_height - max_height)

            # Scroll up if cursor is before visible part.
            if self.vertical_scroll > temp_screen.cursor_position.y:
                self.vertical_scroll = temp_screen.cursor_position.y

            # Scroll down if cursor is after visible part.
            if self.vertical_scroll <= temp_screen.cursor_position.y - max_height:
                self.vertical_scroll = (temp_screen.cursor_position.y + 1) - max_height

            # Scroll down if we need space for the menu.
            if self.need_to_show_completion_menu(cli):
                menu_size = self.menus[0].get_height(self._line(cli).complete_state)
                if temp_screen.cursor_position.y - self.vertical_scroll >= max_height - menu_size:
                    self.vertical_scroll = (temp_screen.cursor_position.y + 1) - (max_height - menu_size)

        # Now copy the region we need to the real screen.
        y = 0
        for y in range(0, min(max_height, temp_screen.current_height - self.vertical_scroll)):
            if self.left_margin:
                # Write left margin. (XXX: line numbers are still not correct in case of line wraps!!!)
                screen._y = y + top_margin
                screen._x = 0
                self.left_margin.write(cli, screen, y, y + self.vertical_scroll)

            # Write line content.
            for x in range(0, temp_screen.size.columns):
                screen._buffer[y + top_margin][x + left_margin_width] = temp_screen._buffer[y + self.vertical_scroll][x]

        screen.cursor_position = Point(y=temp_screen.cursor_position.y - self.vertical_scroll + top_margin,
                                       x=temp_screen.cursor_position.x + left_margin_width)

        y_after_input = y + top_margin

        # Show completion menu.
        if not is_done and self.need_to_show_completion_menu(cli):
            y, x = temp_screen._cursor_mappings[self._line(cli).complete_state.original_document.cursor_position]
            self.menus[0].write(screen, (y - self.vertical_scroll + top_margin, x + left_margin_width), self._line(cli).complete_state)

        return_value = max([min_height + top_margin, screen.current_height])

        # Fill up with tildes.
        if not is_done and self.show_tildes:
            y = y_after_input + 1
            max_ = max([min_height, screen.current_height]) + top_margin
            while y < max_:
                screen.write_at_pos(y, 1, Char('~', Token.Layout.Tilde))
                y += 1

        return return_value

    def need_to_show_completion_menu(self, cli): # XXX: remove
        return self.menus and self._line(cli).complete_state

    def write_to_screen(self, cli, screen, min_height):
        """
        Render the prompt to a `Screen` instance.

        :param screen: The :class:`Screen` class into which we write the output.
        :param min__height: The space (amount of rows) available from the
                            top of the prompt, until the bottom of the
                            terminal. We don't have to use them, but we can.
        """
        # Filter on visible toolbars.
        top_toolbars = [b for b in self.top_toolbars if b.is_visible(cli)]
        bottom_toolbars = [b for b in self.bottom_toolbars if b.is_visible(cli)]

        # Write top toolbars.
        for i, t in enumerate(top_toolbars):
            screen._y, screen._x = i, 0
            t.write(cli, screen)

        # Write actual content (scrolled).
        y = self.write_input_scrolled(cli, screen,
                                      lambda scr : self.write_content(cli, scr),
                                      min_height=max(self.min_height, min_height),
                                      top_margin=len(top_toolbars),
                                      bottom_margin=len(bottom_toolbars))

        # Write bottom toolbars.
        for i, t in enumerate(bottom_toolbars):
            screen._y, screen._x = y + i, 0
            t.write(cli, screen)

    def write_content(self, cli, screen):
        """
        Write the actual content at the current position at the screen.
        """
        if self.before_input is not None:
            self.before_input.write(cli, screen)

        self._write_input(cli, screen)

        if self.after_input is not None:
            self.after_input.write(cli, screen)

