from __future__ import unicode_literals

from ...completion import Completer, Completion
from .rules import TokenStream
from .lexer import lex_document


class ShellCompleter(Completer):
    """
    """
    def __init__(self, grammar):
        self.grammar = grammar

    def get_completions(self, document):
        parts, last_part_token = lex_document(document, only_before_cursor=True)

        def wrap_completion(c):
                    # TODO: extend 'Completion' class to contain flag whether
                    #       the completion is 'complete', so whether we should
                    #       add a space.
            if last_part_token.inside_double_quotes:
                return Completion(c.text + '" ', c.start_position, display=c.text)

            elif last_part_token.inside_single_quotes:
                return Completion(c.text + "' ", c.start_position, display=c.text)
            else:
                return Completion(c.text + " ", c.start_position, display=c.text)

        # Parse grammar
        stream = TokenStream(parts)

        # For any possible parse tre
        for tree in self.grammar.parse(stream):
            for c in tree.complete(last_part_token.unescaped_text):
                yield wrap_completion(c)
