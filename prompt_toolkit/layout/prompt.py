from __future__ import unicode_literals

from pygments.token import Token
from ..enums import IncrementalSearchDirection, InputMode

__all__ = (
    'Prompt',
    'DefaultPrompt',
)


class _ISearch(object):
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
                (Token.Prompt.ISearch.Text.NoMatch, text[index:])
            ]

    @property
    def after(self):
        return [(Token.Prompt.ISearch, '`: ')]

    def get_tokens(self):
        return self.before + self.text + self.after


class Prompt(object):
    """
    Text to show before the actual input.
    """
    def __init__(self, text='> ', token=Token.Prompt.BeforeInput):
        self.text = text
        self.token = token

    def write(self, cli, screen):
        screen.write_highlighted(self.tokens(cli))

    def tokens(self, cli):
        """
        Tokens for the default prompt.
        """
        return [(self.token, self.text)]


class DefaultPrompt(Prompt):
    """
    Default prompt. This one shows the 'arg' and reverse search like
    Bash/readline normally do.
    """
    #: Class responsible for the composition of the i-search tokens.
    isearch_composer = _ISearch

    def tokens(self, cli):
        """
        List of (Token, text) tuples.
        """
        if cli.input_processor.input_mode == InputMode.INCREMENTAL_SEARCH and cli.line.isearch_state:
            return self.isearch_prompt(cli.line.isearch_state)

        elif cli.input_processor.input_mode == InputMode.VI_SEARCH:
            return self.vi_search_prompt()

        elif cli.input_processor.arg is not None:
            return self.arg_prompt(cli.input_processor.arg)

        else:
            return super(DefaultPrompt, self).tokens(cli)

    def arg_prompt(self, arg):
        """
        Tokens for the arg-prompt.
        """
        return [
            (Token.Prompt.Arg, '(arg: '),
            (Token.Prompt.Arg.Text, str(arg)),
            (Token.Prompt.Arg, ') '),
        ]

    def isearch_prompt(self, isearch_state):
        """
        Tokens for the prompt when we go in reverse-i-search mode.
        """
        return self.isearch_composer(isearch_state).get_tokens()

    def vi_search_prompt(self):
        # TODO
        return []
