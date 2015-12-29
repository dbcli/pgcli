"""
Highlighters for usage in a BufferControl.

Highlighters are very similar to processors, but they are applied after the
BufferControl created a screen instance. (Instead of right before creating the screen.)
Highlighters can't change the content of the screen, but they can mark regions
(start_pos, end_pos) as highlighted, using a certain Token.

When possible, it's adviced to use a Highlighter instead of a Processor,
because most of the highlighting code is applied only to the visible region of
the screen. (The Window class will apply the highlighting to the visible region.)
"""
from __future__ import unicode_literals
from pygments.token import Token
from abc import ABCMeta, abstractmethod
from six import with_metaclass

from prompt_toolkit.document import Document
from prompt_toolkit.enums import SEARCH_BUFFER
from prompt_toolkit.filters import to_cli_filter

__all__ = (
    'Fragment',
    'SelectionHighlighter',
    'SearchHighlighter',
    'MatchingBracketHighlighter',
    'ConditionalHighlighter',
)


class Fragment(object):
    """
    Highlight fragment.

    :param start: (int) Cursor start position.
    :param end: (int) Cursor end position.
    :param token: Pygments Token.
    """
    def __init__(self, start, end, token):
        self.start = start
        self.end = end
        self.token = token

    def __repr__(self):
        return 'Fragment(%r, %r, %r)' % (self.start, self.end, self.token)


class Highlighter(with_metaclass(ABCMeta, object)):
    @abstractmethod
    def get_fragments(self, cli, document):
        """
        Return a list of :class:`.Fragment` instances.
        (This can be a generator as well.)
        """
        return []


class SelectionHighlighter(Highlighter):
    """
    Highlight the selection.
    """
    def get_fragments(self, cli, document):
        for from_, to in document.selection_ranges():
            yield Fragment(from_, to + 1, Token.SelectedText)

    def invalidation_hash(self, cli, document):
        # When the selection changes, highlighting will be different.
        return (document.selection and (
            document.cursor_position,
            document.selection.original_cursor_position,
            document.selection.type))


class SearchHighlighter(Highlighter):
    """
    Highlight search matches in the document.

    :param preview_search: A Filter; when active it indicates that we take
        the search text in real time while the user is typing, instead of the
        last active search state.
    :param get_search_state: (Optional) Callable that takes a
        CommandLineInterface and returns the SearchState to be used for the highlighting.
    """
    def __init__(self, preview_search=False, search_buffer_name=SEARCH_BUFFER,
                 get_search_state=None):
        self.preview_search = to_cli_filter(preview_search)
        self.search_buffer_name = search_buffer_name
        self.get_search_state = get_search_state

    def _get_search_text(self, cli):
        """
        The text we are searching for.
        """
        # When the search buffer has focus, take that text.
        if self.preview_search(cli) and cli.buffers[self.search_buffer_name].text:
            return cli.buffers[self.search_buffer_name].text
        # Otherwise, take the text of the last active search.
        elif self.get_search_state:
            return self.get_search_state(cli).text
        else:
            return cli.search_state.text

    def get_fragments(self, cli, document):
        search_text = self._get_search_text(cli)
        ignore_case = cli.is_ignoring_case

        if search_text and not cli.is_returning:
            for index in document.find_all(search_text, ignore_case=ignore_case):
                if index == document.cursor_position:
                    token = Token.SearchMatch.Current
                else:
                    token = Token.SearchMatch

                yield Fragment(index, index + len(search_text), token)

    def invalidation_hash(self, cli, document):
        search_text = self._get_search_text(cli)

        # When the search state changes, highlighting will be different.
        return (
            search_text,
            cli.is_returning,

            # When we search for text, and the cursor position changes. The
            # processor has to be applied every time again, because the current
            # match is highlighted in another color.
            (search_text and document.cursor_position),
        )


class ConditionalHighlighter(Highlighter):
    """
    Highlighter that applies another highlighter, according to a certain condition.

    :param highlighter: :class:`.Highlighter` instance.
    :param filter: :class:`~prompt_toolkit.filters.CLIFilter` instance.
    """
    def __init__(self, highlighter, filter):
        assert isinstance(highlighter, Highlighter)

        self.highlighter = highlighter
        self.filter = to_cli_filter(filter)

    def get_fragments(self, cli, document):
        if self.filter(cli):
            return self.highlighter.get_fragments(cli, document)
        else:
            return []

    def invalidation_hash(self, cli, document):
        # When enabled, use the hash of the highlighter. Otherwise, just use
        # False.
        if self.filter(cli):
            return (True, self.highlighter.invalidation_hash(cli, document))
        else:
            return False


class MatchingBracketHighlighter(Highlighter):
    """
    When the cursor is on or right after a bracket, it highlights the matching
    bracket.
    """
    _closing_braces = '])}>'

    def __init__(self, chars='[](){}<>'):
        self.chars = chars

    def get_fragments(self, cli, document):
        result = []

        def replace_token(pos):
            """ Replace token in list of tokens. """
            result.append(Fragment(pos, pos + 1, Token.MatchingBracket))

        def apply_for_document(document):
            """ Find and replace matching tokens. """
            if document.current_char in self.chars:
                pos = document.matching_bracket_position

                if pos:
                    replace_token(document.cursor_position)
                    replace_token(document.cursor_position + pos)
                    return True

        # Apply for character below cursor.
        applied = apply_for_document(document)

        # Otherwise, apply for character before cursor.
        if (not applied and document.cursor_position > 0 and
                document.char_before_cursor in self._closing_braces):
            apply_for_document(Document(document.text, document.cursor_position - 1))

        return result

    def invalidation_hash(self, cli, document):
        on_brace = document.current_char in self.chars
        after_brace = document.char_before_cursor in self.chars

        if on_brace:
            return (True, document.cursor_position)
        elif after_brace and document.char_before_cursor in self._closing_braces:
            return (True, document.cursor_position - 1)
        else:
            # Don't include the cursor position in the hash if we are not *on*
            # a brace. We don't have to rerender the output, because it will be
            # the same anyway.
            return False
