from __future__ import unicode_literals

from pygments.token import Token

from .rules import TokenStream
from .lexer import lex_document


class CompletionHint(object):
    def __init__(self, grammar):
        self.grammar = grammar

    def write(self, cli, screen):
        if not (cli.is_exiting or cli.is_aborting or cli.is_returning):
            screen.write_highlighted(self.tokens(cli))

    def tokens(self, cli):
        def _():
            document = cli.line.document
            parts, last_part_token = lex_document(document, only_before_cursor=False)

            # Don't show help when you're in the middle of typing a 'token'.
            # (Show after having typed the space, or at the start of the line.)
            if not last_part_token.unescaped_text:
                # Parse grammar
                stream = TokenStream(parts)
                trees = list(self.grammar.parse(stream))

                # print (trees) ### debug

                if len(trees) > 1:
                    yield (Token.Placeholder.Bracket, '[')

                first = True

                for tree in trees:
                    if not first:
                        yield (Token.Placeholder.Separator, '|')
                    first = False

                    for t in tree.get_help_tokens():
                        yield t

                if len(trees) > 1:
                    yield (Token.Placeholder.Bracket, ']')
        return list(_())
