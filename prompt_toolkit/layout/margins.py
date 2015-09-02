"""
Margin implementations for a `BufferControl`.
"""
from __future__ import unicode_literals

from six import with_metaclass
from abc import ABCMeta, abstractmethod

from prompt_toolkit.filters import to_cli_filter
from pygments.token import Token

__all__ = (
    'Margin',
    'NumberredMargin',
    'NoMargin',
    'ConditionalMargin',
)


class _NumberedMarginTokenCache(dict):
    """
    Cache for numbered margins.
    Maps (width, line_number) to a list of tokens.
    """
    def __missing__(self, key):
        width, line_number = key

        if line_number is not None:
            tokens = [(Token.LineNumber, u'%%%si ' % width % (line_number + 1))]
        else:
            tokens = [(Token.LineNumber, ' ' * (width + 1))]

        self[key] = tokens
        return tokens

_NUMBERED_MARGIN_TOKEN_CACHE = _NumberedMarginTokenCache()


class Margin(with_metaclass(ABCMeta, object)):
    """
    Base interface for a margin.
    """
    @abstractmethod
    def create_handler(self, cli, document):
        """
        Return a callable that takes a line number and returns the tokens to
        be displayed in front of that line.

        This function will also be called with `line_number` equal to `None`
        after a line wrap.
        """
        def margin(line_number):
            return []
        return margin

    def invalidation_hash(self, cli, document):
        return None


class NumberredMargin(Margin):
    """
    Simple margin that shows the line numbers.
    """
    def create_handler(self, cli, document):
        decimals = max(3, len('%s' % document.line_count))

        def margin(line_number):
            return _NUMBERED_MARGIN_TOKEN_CACHE[decimals, line_number]
        return margin


class ConditionalMargin(Margin):
    """
    Wrapper around other `Margin` classes to show/hide them.
    """
    def __init__(self, margin, filter):
        assert isinstance(margin, Margin)

        self.margin = margin
        self.filter = to_cli_filter(filter)

    def invalidation_hash(self, cli, document):
        return self.filter(cli)

    def create_handler(self, cli, document):
        if self.filter(cli):
            return self.margin.create_handler(cli, document)
        else:
            return NoMargin().create_handler(cli, document)


class NoMargin(Margin):
    """
    Empty margin.
    """
    def create_handler(self, cli, document):
        def margin(line_number):
            return []
        return margin
