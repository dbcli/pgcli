from __future__ import unicode_literals

from pygments.token import Token
from prompt_toolkit.code import Code, Completion

from .rules import Sequence, Literal, TokenStream
from .lexer import TextToken, ParametersLexer


# TODO: pressing enter when the last token is in a quote should insert newline.


class ShellCode(Code):
    rule = Sequence([ Literal('Hello'), Literal('World') ])

    def _get_tokens(self):
        return list(ParametersLexer(stripnl=False, stripall=False, ensurenl=False).get_tokens(self.text))

    def _get_lex_result(self, only_before_cursor=False):
        # Take Text tokens before cursor
        if only_before_cursor:
            tokens = self.get_tokens_before_cursor()
        else:
            tokens = self.get_tokens()
        parts = [ t[1] for t in tokens if t[0] in Token.Text ]

        # Separete the last token (where we are currently one)
        starting_new_token = not tokens or tokens[-1][0] in Token.WhiteSpace
        if starting_new_token:
            last_part = ''
        else:
            last_part = parts.pop()

        # Unescape tokens
        parts = [ TextToken(t).unescaped_text for t in parts ]
        last_part_token = TextToken(last_part)

        return parts, last_part_token


    def get_completions(self, recursive=False):
        parts, last_part_token = self._get_lex_result(only_before_cursor=True)

        def wrap_completion(c):
                    # TODO: extend 'Completion' class to contain flag whether
                    #       the completion is 'complete', so whether we should
                    #       add a space.
            if last_part_token.inside_double_quotes:
                return Completion(c.display, c.suffix + '" ')

            elif last_part_token.inside_single_quotes:
                return Completion(c.display, c.suffix + "' ")
            else:
                return Completion(c.display, c.suffix + " ")

        # Parse grammar
        stream = TokenStream(parts)

        # For any possible parse tre
        for tree in self.rule.parse(stream):
            for c in tree.complete(last_part_token.unescaped_text):
                yield wrap_completion(c)

    def get_parse_info(self):
        parts, last_part_token = self._get_lex_result()
        stream = TokenStream(parts + [ last_part_token.unescaped_text ]) # TODO: raise error when this last token is not finished.

        trees = list(self.rule.parse(stream))

        if len(trees) == 1:
            return(trees[0])
        else:
            raise Exception('Invalid command.') # TODO: raise better exception.
