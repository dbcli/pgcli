from __future__ import unicode_literals

from pygments.token import Token

__all__ = (
    'LeftMargin',
    'LeftMarginWithLineNumbers',
)


class LeftMargin(object):
    def __init__(self, width=10, token=None):
        self._width = width
        self.token = token or Token.Layout.LeftMargin

    def width(self, cli):
        return self._width

    def write(self, cli, screen, y, line_number):
        screen.write_highlighted([
            (self.token, '.' * self.width)
        ])


class LeftMarginWithLineNumbers(LeftMargin):
    def write(self, cli, screen, y, line_number):
        screen.write_highlighted([
            (self.token, '%%%ii. ' % (self.width(cli) - 2) % (line_number + 1)),
        ])
