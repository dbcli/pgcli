from __future__ import unicode_literals

from pygments.lexers import BashLexer
from pygments.token import Token

from ..enums import IncrementalSearchDirection
from ..layout import Layout
from ..layout.prompt import Prompt

from .utils import fit_tokens_in_size

__all__ = (
    'ArgToolbar',
    'CompletionsToolbar',
    'SearchToolbar',
    'SystemToolbar',
    'TextToolbar',
    'Toolbar',
)


class Toolbar(object):
    def __init__(self, token=None, height=1):
        self.token = token or Token.Toolbar
        self.height = height

    def write(self, cli, screen):
        width = screen.size.columns
        tokens = self.get_tokens(cli, width)

        # Make sure that this list of tokens fit the amount of columns and rows.
        token_lines = fit_tokens_in_size(
            tokens, width=screen.size.columns, height=self.height,
            default_token=self.token)

        # Write to screen.
        y = screen._y
        for i, tokens in enumerate(token_lines):
            screen._y = y + i
            screen._x = 0
            screen.write_highlighted(tokens)

    def is_visible(self, cli):
        return not (cli.is_exiting or cli.is_aborting or cli.is_returning)

    def get_tokens(self, cli, width):
        return []


class TextToolbar(Toolbar):
    """
    :param text: The text to be displayed.
    :param token: Default token for the text.
    :param lexer: (optional) Pygments lexer for highlighting of the text.
    """
    def __init__(self, text='', token=None, height=1, lexer=None):
        super(TextToolbar, self).__init__(token=token, height=height)
        self.text = text

        if lexer:
            self.lexer = lexer(
                stripnl=False,
                stripall=False,
                ensurenl=False)
        else:
            self.lexer = None

    def get_tokens(self, cli, width):
        if self.lexer is None:
            return [(self.token, self.text)]
        else:
            return list(self.lexer.get_tokens(self.text))


class ArgToolbar(Toolbar):
    """
    A simple toolbar which shows the repeat 'arg'.
    """
    def __init__(self, token=None):
        token = token or Token.Toolbar.Arg
        super(ArgToolbar, self).__init__(token=token)

    def is_visible(self, cli):
        return super(ArgToolbar, self).is_visible(cli) and \
            cli.input_processor.arg is not None

    def get_tokens(self, cli, width):
        return [
            (Token.Toolbar.Arg, 'Repeat: '),
            (Token.Toolbar.Arg.Text, str(cli.input_processor.arg)),
        ]


class SystemToolbar(Toolbar):
    """
    The system toolbar. Shows the '!'-prompt.
    """
    def __init__(self, buffer_name='system'):
        token = Token.Toolbar.System
        super(SystemToolbar, self).__init__(token=token)

        # We use a nested single-line-no-wrap layout for this.
        self.layout = Layout(before_input=Prompt('Shell command: ', token=token.Prefix),
                             lexer=BashLexer,
                             buffer_name='system')
        self.buffer_name = buffer_name

    def is_visible(self, cli):
        return super(SystemToolbar, self).is_visible(cli) and \
            cli.focus_stack.current == self.buffer_name

    def write(self, cli, screen):
        # Just write this layout at the current position.
        # XXX: Make sure that we don't have multiline here. Force layout to be single line.
        self.layout.write_content(cli, screen)


class SearchToolbar(Toolbar):
    def __init__(self, token=None, buffer_name='search'):
        token = token or Token.Toolbar.Search
        super(SearchToolbar, self).__init__(token=token)

        self.buffer_name = buffer_name

        class Prefix(Prompt):
            """ Search prompt. """
            def tokens(self, cli):
                buffer = cli.buffers[cli.focus_stack.previous]

                if buffer.isearch_state is None:
                    text = ''
                elif buffer.isearch_state.isearch_direction == IncrementalSearchDirection.BACKWARD:
                    text = 'I-search backward: '
                else:
                    text = 'I-search: '

                return [(token, text)]

        class SearchLayout(Layout):
            def get_input_tokens(self, cli):
                buffer = cli.buffers[cli.focus_stack.previous]

                search_buffer = cli.buffers[self.buffer_name]
                index = buffer.isearch_state and buffer.isearch_state.no_match_from_index

                if index is None:
                    return [(token.Text, search_buffer.text)]
                else:
                    return [
                        (token.Text, search_buffer.text[:index]),
                        (token.Text.NoMatch, search_buffer.text[index:]),
                    ]

        self.layout = SearchLayout(before_input=Prefix(), buffer_name=self.buffer_name)

    def is_visible(self, cli):
        return super(SearchToolbar, self).is_visible(cli) and \
            cli.focus_stack.current == self.buffer_name

    def write(self, cli, screen):
        self.layout.write_content(cli, screen)


class CompletionsToolbar(Toolbar):
    """
    Helper for drawing the completion menu 'wildmenu'-style.
    (Similar to Vim's wildmenu.)
    """
    def __init__(self, token=None, buffer_name='default'):
        token = token or Token.Toolbar.Completions
        super(CompletionsToolbar, self).__init__(token=token)
        self.buffer_name = buffer_name

    def is_visible(self, cli):
        return super(CompletionsToolbar, self).is_visible(cli) and \
            bool(cli.buffers[self.buffer_name].complete_state) and \
            len(cli.buffers[self.buffer_name].complete_state.current_completions) >= 1

    def get_tokens(self, cli, width):
        """
        Write the menu to the screen object.
        """
        complete_state = cli.buffers[self.buffer_name].complete_state
        completions = complete_state.current_completions
        index = complete_state.complete_index  # Can be None!

        # Don't draw the menu if there is just one completion.
        if len(completions) <= 1:
            return []

        # Width of the completions without the left/right arrows in the margins.
        content_width = width - 6

        # Booleans indicating whether we stripped from the left/right
        cut_left = False
        cut_right = False

        # Create Menu content.
        tokens = []

        for i, c in enumerate(completions):
            # When there is no more place for the next completion
            if len(tokens) + len(c.display) >= content_width:
                # If the current one was not yet displayed, page to the next sequence.
                if i <= (index or 0):
                    tokens = []
                    cut_left = True
                # If the current one is visible, stop here.
                else:
                    cut_right = True
                    break

            tokens.append((self.token.Completion.Current if i == index else self.token.Completion, c.display))
            tokens.append((self.token, ' '))

        # Extend/strip until the content width.
        tokens.append((self.token, ' ' * (content_width - len(tokens))))
        tokens = tokens[:content_width]

        # Return tokens
        return [
            (self.token, ' '),
            (self.token.Arrow, '<' if cut_left else ' '),
            (self.token, ' '),
        ] + tokens + [
            (self.token, ' '),
            (self.token.Arrow, '>' if cut_right else ' '),
            (self.token, ' '),
        ]


class ValidationToolbar(Toolbar):
    """
    Toolbar for displaying validation errors.
    """
    def __init__(self, token=None, buffer_name='default'):
        token = token or Token.Toolbar.Validation
        super(ValidationToolbar, self).__init__(token=token)
        self.buffer_name = buffer_name

    def is_visible(self, cli):
        return super(ValidationToolbar, self).is_visible(cli) and \
            bool(cli.current_buffer.validation_error)

    def get_tokens(self, cli, width):
        buffer = cli.buffers[self.buffer_name]

        if buffer.validation_error:
            row, column = buffer.document.translate_index_to_position(
                buffer.validation_error.index)

            text = '%s (line=%s column=%s)' % (
                buffer.validation_error.message, row, column)
            return [(self.token, text)]
        else:
            return []
