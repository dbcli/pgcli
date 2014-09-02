"""
Prompt representation.
"""
from __future__ import unicode_literals

from pygments.token import Token
from .enums import IncrementalSearchDirection, LineMode

__all__ = (
    'HorizontalCompletionMenu',
    'PopupCompletionMenu',
    'Prompt',
    'TokenList',
    'PasswordProcessor',
    'BracketsMismatchProcessor',
)

class TokenList(object):
    """
    Wrapper around (Token, text) tuples.
    Implements logical slice and len operations.
    """
    def __init__(self, iterator=None):
        if iterator is not None:
            self._list = list(iterator)
        else:
            self._list = []

    def __len__(self):
        return sum(len(v) for k, v in self._list)

    def __getitem__(self, val):
        result = []

        for token, string in self._list:
            for c in string:
                result.append((token, c))

        if isinstance(val, slice):
            return TokenList(result[val])
        else:
            return result[val]

    def __iter__(self):
        return iter(self._list)

    def append(self, val):
        self._list.append(val)

    def __add__(self, other):
        return TokenList(self._list + list(other))

    @property
    def text(self):
        return ''.join(p[1] for p in self._list)

    def __repr__(self):
        return 'TokenList(%r)' % self._list


class HorizontalCompletionMenu(object):
    """
    Helper for drawing the completion menu 'wildmenu'-style. (Similar to Vim's wildmenu.)
    """
    def write(self, screen, complete_cursor_position, complete_state):
        """
        Write the menu to the screen object.
        """
        completions = complete_state.current_completions
        index = complete_state.complete_index # Can be None!

        # Width of the completions without the left/right arrows in the margins.
        content_width = screen.columns - 6

        # Booleans indicating whether we stripped from the left/right
        cut_left = False
        cut_right = False

        # Create Menu content.
        tokens = TokenList()

        for i, c in enumerate(completions):
            # When there is no more place for the next completion
            if len(tokens) + len(c.display) >= content_width:
                # If the current one was not yet displayed, page to the next sequence.
                if i <= (index or 0):
                    tokens = TokenList()
                    cut_left = True
                # If the current one is visible, stop here.
                else:
                    cut_right = True
                    break

            tokens.append((Token.WildMenu.CurrentCompletion if i == index else Token.WildMenu.Completion, c.display))
            tokens.append((Token.WildMenu, ' '))

        # Extend/strip until the content width.
        tokens.append((Token.WildMenu, ' ' * (content_width - len(tokens))))
        tokens = tokens[:content_width]

        # Draw to screen.
        screen.write_highlighted([
                        (Token.WildMenu, ' '),
                        (Token.WildMenu.Arrow, '<' if cut_left else ' '),
                        (Token.WildMenu, ' '),
                    ])
        screen.write_highlighted(tokens)
        screen.write_highlighted([
                        (Token.WildMenu, ' '),
                        (Token.WildMenu.Arrow, '>' if cut_right else ' '),
                        (Token.WildMenu, ' '),
                    ])


class PopupCompletionMenu(object):
    """
    Helper for drawing the complete menu to the screen.
    """
    current_completion_token = Token.CompletionMenu.CurrentCompletion
    completion_token = Token.CompletionMenu.Completion

    progress_button_token = Token.CompletionMenu.ProgressButton
    progress_bar_token = Token.CompletionMenu.ProgressBar

    def __init__(self, max_height=5):
        self.max_height = max_height

    def write(self, screen, complete_cursor_position, complete_state):
        """
        Write the menu to the screen object.
        """
        completions = complete_state.current_completions
        index = complete_state.complete_index # Can be None!

        # Get position of the menu.
        y, x = complete_cursor_position
        y += 1
        x = max(0, x - 1) # XXX: Don't draw it in the right margin!!!...

        # Calculate width of completions menu.
        menu_width = self.get_menu_width(complete_state)

        # Decide which slice of completions to show.
        if len(completions) > self.max_height and (index or 0) > self.max_height / 2:
            slice_from = min(
                        (index or 0) - self.max_height // 2, # In the middle.
                        len(completions) - self.max_height # At the bottom.
                    )
        else:
            slice_from = 0

        slice_to = min(slice_from + self.max_height, len(completions))

        # Create a function which decides at which positions the scroll button should be shown.
        def is_scroll_button(row):
            items_per_row = float(len(completions)) / min(len(completions), self.max_height)
            items_on_this_row_from = row * items_per_row
            items_on_this_row_to = (row + 1) * items_per_row
            return items_on_this_row_from <= (index or 0) < items_on_this_row_to

        # Write completions to screen.
        for i, c in enumerate(completions[slice_from:slice_to]):
            is_current_completion = (i + slice_from == index)

            if is_scroll_button(i):
                button_token = self.progress_button_token
            else:
                button_token = self.progress_bar_token

            tokens = [(Token, ' ')] + \
                     self.get_menu_item_tokens(c, is_current_completion, menu_width) + \
                     [(button_token, ' '), (Token, ' ')]

            screen.write_highlighted_at_pos(y+i, x, tokens, z_index=10)

    def get_menu_width(self, complete_state):
        """
        Calculate the menu width. This is passed to `get_menu_item_tokens`.
        """
        return max(len(c.display) for c in complete_state.current_completions)

    def get_menu_item_tokens(self, completion, is_current_completion, menu_width):
        if is_current_completion:
            token = self.current_completion_token
        else:
            token = self.completion_token

        return [(token, ' %%-%is ' % menu_width % completion.display)]


class PasswordProcessor(object):
    """
    Processor that turns masks the input. (For passwords.)
    """
    def __init__(self, char='*'):
        self.char = char

    def process_tokens(self, tokens):
        return [(token, self.char * len(text)) for token, text in tokens]


class BracketsMismatchProcessor(object):
    """
    Processor that replaces the token type of bracket mismatches by an Error.
    """
    error_token = Token.Error

    def process_tokens(self, tokens):
        tokens = list(TokenList(tokens))

        stack = [] # Pointers to the result array

        for index, (token, text) in enumerate(tokens):
            top = tokens[stack[-1]][1] if stack else ''

            if text in '({[]})':
                if text in '({[':
                    # Put open bracket on the stack
                    stack.append(index)

                elif (text == ')' and top == '(' or
                      text == '}' and top == '{' or
                      text == ']' and top == '['):
                    # Match found
                    stack.pop()
                else:
                    # No match for closing bracket.
                    tokens[index] = (self.error_token, text)

        # Highlight unclosed tags that are still on the stack.
        for index in stack:
            tokens[index] = (Token.Error, tokens[index][1])

        return tokens


class ISearchComposer(object):
    def __init__(self, isearch_state):
        self.isearch_state = isearch_state

    @property
    def before(self):
        if self.isearch_state.isearch_direction == IncrementalSearchDirection.BACKWARD:
            text = 'reverse-i-search'
        else:
            text = 'i-search'

        return [(Token.Prompt.ISearch, '(%s)`' % text)]

    @property
    def text(self):
        index = self.isearch_state.no_match_from_index
        text = self.isearch_state.isearch_text

        if index is None:
            return [(Token.Prompt.ISearch.Text, text)]
        else:
            return [
                    (Token.Prompt.ISearch.Text, text[:index]),
                    (Token.Prompt.ISearch.TextNoMatch, text[index:])
            ]

    @property
    def after(self):
        return [(Token.Prompt.ISearch, '`: ')]

    def get_tokens(self):
        return self.before + self.text + self.after


class Prompt(object):
    """
    Base class for a valid prompt.

    :attr render_context: :class:`~prompt_toolkit.render_context.RenderContext` instance.
    """
    #: Menu class for autocompletions. This can be `None`
    completion_menu = PopupCompletionMenu()

    #: Text to show before the input
    prompt_text = '> '

    #: Processors for transforming the tokens received from the `Code` object.
    #: (This can be used for displaying password input as '*' or for
    #: highlighting mismatches of brackets in case of Python input.)
    input_processors = []

    #: Class responsible for the composition of the i-search tokens.
    isearch_composer = ISearchComposer

    def __init__(self, render_context): # Wrap line/code in render_context
        self.render_context = render_context
        self.line = render_context.line # XXX: remove

    @property
    def tokens_before_input(self):
        """
        Text shown before the actual input.
        List of (Token, text) tuples.
        """
        if self.line.mode == LineMode.INCREMENTAL_SEARCH:
            return self.isearch_prompt
        elif self.line._arg_prompt_text:
            return self.arg_prompt
        else:
            return self.default_prompt

    @property
    def default_prompt(self):
        """
        Tokens for the default prompt.
        """
        return [(Token.Prompt, self.prompt_text)]

    @property
    def arg_prompt(self):
        """
        Tokens for the arg-prompt.
        """
        return [
            (Token.Prompt.Arg, '(arg: '),
            (Token.Prompt.ArgText, str(self.line._arg_prompt_text)),
            (Token.Prompt.Arg, ') '),
        ]

    @property
    def isearch_prompt(self):
        """
        Tokens for the prompt when we go in reverse-i-search mode.
        """
        return self.isearch_composer(self.line.isearch_state).get_tokens()

    @property
    def tokens_after_input(self):
        """
        List of (Token, text) tuples for after the inut.
        (This can be used to create a help text or a status line.)
        """
        return []

    @property
    def tokens_in_left_margin(self):
        """
        When the renderer has to render the command line over several lines
        because the input contains newline characters. This prefix will be
        inserted before each line.

        This is a generator of (Token, text) tuples.
        """
        # Take the length of the default prompt.
        prompt_text = TokenList(self.tokens_before_input).text
        length = len(prompt_text.rstrip())
        spaces = len(prompt_text) - length

        yield (Token.Prompt.SecondLinePrefix, '.' * length)
        yield (Token.Prompt.SecondLinePrefix, ' ' * spaces)

    def create_left_input_margin(self, screen, row):
        screen.write_highlighted(self.tokens_in_left_margin)

    def write_before_input(self, screen):
        screen.write_highlighted(self.tokens_before_input)

    @property
    def input_tokens(self):
        tokens = self.render_context.code_obj.get_tokens()

        for p in self.input_processors:
            tokens = p.process_tokens(tokens)

        return tokens

    def write_input(self, screen):
        # Set second line prefix
        screen.set_left_margin(lambda row: self.create_left_input_margin(screen, row))

        index = 0
            # Note, we add the space character at the end, because that's where
            #       the cursor could be.
        for token, text in self.input_tokens + [(Token, ' ')]:
            for c in text:
                # Determine Token-type for character.
                t = self.render_context.highlighted_characters.get(index, token)

                # Insert char.
                screen.write_char(c, t,
                                string_index=index,
                                set_cursor_position=(index == self.line.cursor_position)
                        )

                index += 1

        # Unset left margin.
        screen.set_left_margin(None)

    def write_after_input(self, screen):
        # Write help text.
        if not (self.render_context.accept or self.render_context.abort):
            help_tokens = self.tokens_after_input
            if help_tokens:
                screen.write_highlighted(help_tokens)

    def write_menus(self, screen):
        render_context = self.render_context

        # Write completion menu.
        if self.completion_menu and render_context.complete_state:
            # Calculate the position where the cursor was, the moment that we pressed the complete button (tab).
            complete_cursor_position = screen._cursor_mappings[render_context.complete_state.original_document.cursor_position]

            self.completion_menu.write(screen, complete_cursor_position, render_context.complete_state)

    def write_to_screen(self, screen, last_screen_height):
        """
        Render the prompt to a `Screen` instance.
        """
        self.write_before_input(screen)
        self.write_input(screen)
        self.write_after_input(screen)
        self.write_menus(screen)
