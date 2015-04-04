from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

from pygments.token import Token
from .utils import token_list_len
from prompt_toolkit.document import Document

__all__ = (
    'HighlightSearchProcessor',
    'HighlightSelectionProcessor',
    'PasswordProcessor',
    'BracketsMismatchProcessor',
    'BeforeInput',
    'AfterInput',
)


class Processor(with_metaclass(ABCMeta, object)):
    """
    Manipulate the tokenstream for a `BufferControl`.
    """
    @abstractmethod
    def run(self, cli, buffer, tokens):
        return tokens, lambda i: i

    def invalidation_hash(self, cli, buffer):
        return None


class HighlightSearchProcessor(Processor):
    """
    Processor that highlights search matches in the document.
    """
    def run(self, cli, buffer, tokens):
        isearch_state = buffer.isearch_state

        if isearch_state:
            # For each search match, replace the Token.
            for index in buffer.document.find_all(isearch_state.isearch_text):
                if index == buffer.cursor_position:
                    token = Token.SearchMatch.Current
                else:
                    token = Token.SearchMatch

                for x in range(index, index + len(isearch_state.isearch_text)):
                    tokens[x] = (token, tokens[x][1])

        return tokens, lambda i: i

    def invalidation_hash(self, cli, buffer):
        # When the search state changes, highlighting will be different.
        return (
            buffer.isearch_state,
            (buffer.isearch_state and buffer.isearch_state.isearch_text),

            # When we search for text, and the cursor position changes. The
            # processor has to be applied every time again, because the current match is highlighted
            # in another color.
            (buffer.isearch_state and buffer.isearch_state.isearch_text and buffer.cursor_position)
        )


class HighlightSelectionProcessor(Processor):
    """
    Processor that highlights the selection in the document.
    """
    def run(self, cli, buffer, tokens):
        # In case of selection, highlight all matches.
        selection_range = buffer.document.selection_range()

        if selection_range:
            from_, to = selection_range

            for i in range(from_, to):
                tokens[i] = (Token.SelectedText, tokens[i][1])

        return tokens, lambda i: i

    def invalidation_hash(self, cli, buffer):
        # When the search state changes, highlighting will be different.
        return (
            buffer.document.selection_range(),
        )


class PasswordProcessor(Processor):
    """
    Processor that turns masks the input. (For passwords.)
    """
    def __init__(self, char='*'):
        self.char = char

    def run(self, cli, buffer, tokens):
        # Returns (new_token_list, cursor_index_to_token_index_f)
        return [(token, self.char * len(text)) for token, text in tokens], lambda i: i


class HighlightMatchingBracketProcessor(Processor):
    """
    When the cursor is on or right after a bracket, it highlights the matching
    bracket.
    """
    _closing_braces = '])}>'

    def __init__(self, chars='[](){}<>'):
        self.chars = chars

    def run(self, cli, buffer, tokens):
        def replace_token(pos):
            """ Replace token in list of tokens. """
            tokens[pos] = (Token.MatchingBracket, tokens[pos][1])

        def apply_for_document(document):
            """ Find and replace matching tokens. """
            if document.current_char in self.chars:
                pos = document.matching_bracket_position

                if pos:
                    replace_token(document.cursor_position)
                    replace_token(document.cursor_position + pos)
                    return True

        # Apply for character below cursor.
        d = buffer.document
        applied = apply_for_document(d)

        # Otherwise, apply for character before cursor.
        if not applied and d.cursor_position > 0 and d.char_before_cursor in self._closing_braces:
            apply_for_document(Document(d.text, d.cursor_position - 1))

        return tokens, lambda i: i

    def invalidation_hash(self, cli, buffer):
        on_brace = buffer.document.current_char in self.chars
        after_brace = buffer.document.char_before_cursor in self.chars

        if on_brace:
            return (True, buffer.cursor_position)
        elif after_brace and buffer.document.char_before_cursor in self._closing_braces:
            return (True, buffer.cursor_position - 1)
        else:
            # Don't include the cursor position in the hash if we are not *on*
            # a brace. We don't have to rerender the output, because it will be
            # the same anyway.
            return False


class BracketsMismatchProcessor(Processor):
    """
    Processor that replaces the token type of bracket mismatches by an Error.
    """
    error_token = Token.Error

    def run(self, cli, buffer, tokens):
        stack = []  # Pointers to the result array

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

        return tokens, lambda i: i


class BeforeInput(Processor):
    """
    Insert tokens before the input.
    """
    def __init__(self, get_tokens):
        assert callable(get_tokens)
        self.get_tokens = get_tokens

    def run(self, cli, buffer, tokens):
        tokens_before = self.get_tokens(cli, buffer)
        shift_position = token_list_len(tokens_before)

        return tokens_before + tokens, lambda i: i + shift_position

    @classmethod
    def static(cls, text, token=Token):
        def get_static_tokens(cli, buffer):
            return [(token, text)]
        return cls(get_static_tokens)


class AfterInput(Processor):
    """
    Insert tokens after the input.
    """
    def __init__(self, get_tokens):
        assert callable(get_tokens)
        self.get_tokens = get_tokens

    def run(self, cli, buffer, tokens):
        return tokens + self.get_tokens(cli, buffer), lambda i: i

    @classmethod
    def static(cls, text, token=Token):
        def get_static_tokens(cli, buffer):
            return [(token, text)]
        return cls(get_static_tokens)
