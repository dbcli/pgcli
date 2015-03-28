from __future__ import unicode_literals

from pygments.token import Token
from ..enums import IncrementalSearchDirection
from .utils import token_list_len
from .processors import Processor

__all__ = (
    'DefaultPrompt',
)


class DefaultPrompt(Processor):
    """
    Default prompt. This one shows the 'arg' and reverse search like
    Bash/readline normally do.
    """
    def __init__(self, prompt='> '):
        self.prompt = prompt

    def run(self, cli, buffer, tokens):
        # Get text before cursor.
        if buffer.isearch_state:
            before = _get_isearch_tokens(buffer.isearch_state)

        elif cli.input_processor.arg is not None:
            before = _get_arg_tokens(cli)

        else:
            before = [(Token.Prompt, self.prompt)]

        # Insert before buffer text.
        shift_position = token_list_len(before)

        return before + tokens, lambda i: i + shift_position

    def invalidation_hash(self, cli, buffer):
        return (
            cli.input_processor.arg,
            buffer.isearch_state,
            buffer.isearch_state and buffer.isearch_state.isearch_text,
        )


def _get_isearch_tokens(isearch_state):
    def before():
        if isearch_state.isearch_direction == IncrementalSearchDirection.BACKWARD:
            text = 'reverse-i-search'
        else:
            text = 'i-search'

        return [(Token.Prompt.Search, '(%s)`' % text)]

    def text():
        index = isearch_state.no_match_from_index
        text = isearch_state.isearch_text

        if index is None:
            return [(Token.Prompt.Search.Text, text)]
        else:
            return [
                (Token.Prompt.Search.Text, text[:index]),
                (Token.Prompt.Search.Text.NoMatch, text[index:])
            ]

    def after():
        return [(Token.Prompt.Search, '`: ')]

    return before() + text() + after()


def _get_arg_tokens(cli):
    """
    Tokens for the arg-prompt.
    """
    arg = cli.input_processor.arg

    return [
        (Token.Prompt.Arg, '(arg: '),
        (Token.Prompt.Arg.Text, str(arg)),
        (Token.Prompt.Arg, ') '),
    ]
