from __future__ import unicode_literals, absolute_import
from .commands import completion_hints
from pygments.token import Token


class CompletionHint(object):
    """
    Completion hint to be shown after the input.
    """
    def write(self, cli, screen):
        if not (cli.is_exiting or cli.is_aborting or cli.is_returning):
            screen.write_highlighted(self._tokens(cli))

    def _tokens(self, cli):
        words = cli.line.document.text.split()
        if len(words) == 1:
            word = words[0]

            for commands, help in completion_hints:
                if word in commands:
                    return self._highlight_completion(' ' + help)

        return []

    def _highlight_completion(self, text):
        """
        Choose tokens for special characters in the text of the completion
        hint.
        """
        def highlight_char(c):
            if c in '[:]|.()':
                return Token.CompletionHint.Symbol, c
            else:
                return Token.CompletionHint.Parameter, c
        return [highlight_char(c) for c in text]
