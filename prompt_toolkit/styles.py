"""
Default styling.
This contains the default style from Pygments, but adds the styling for
prompt-toolkit specific Tokens on top.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from collections import namedtuple
from pygments.token import Token
from six import with_metaclass

import pygments.style
import pygments.styles.default

__all__ = (
    'Style',
    'Attrs',
    'DynamicStyle',
    'PygmentsStyle'
    'TokenToAttrsCache',

    'default_style_extensions',
    'DefaultStyle',
)


#: Style attributes.
Attrs = namedtuple('Attrs', 'color bgcolor bold underline reverse')
"""
:param color: Hexadecimal string. E.g. '000000'
:param bgcolor: Hexadecimal string. E.g. 'ffffff'
:param bold: Boolean
:param underline: Boolean
:param reverse: Boolean
"""

_default_attrs = Attrs(color=None, bgcolor=None, bold=False, underline=False, reverse=False)


class Style(with_metaclass(ABCMeta, object)):
    """
    Abstract base class for prompt_toolkit styles.
    """
    @abstractmethod
    def get_token_to_attributes_dict(self):
        """
        This should return a dictionary mapping Token to :class:`.Attrs`.

        (Best to return a :class:`.TokenToAttrsCache`.)
        """

    @abstractmethod
    def invalidation_hash(self):
        """
        Invalidation hash for the style. When this changes over time, the
        renderer knows that something in the style changed, and that everything
        has to be redrawn.
        """


class DynamicStyle(Style):
    """
    Style class that can dynamically returns an other Style.

    :param get_style: Callable that returns a :class:`.Style` instance.
    """
    def __init__(self, get_style):
        self.get_style = get_style

    def get_token_to_attributes_dict(self):
        style = self.get_style()
        assert isinstance(style, Style)

        return style.get_token_to_attributes_dict()

    def invalidation_hash(self):
        return self.get_style().invalidation_hash()


class PygmentsStyle(Style):
    """
    Adaptor for using Pygments styles as a :class:`.Style`.

    :param pygments_style_cls: Pygments ``Style`` class.
    """
    def __init__(self, pygmens_style_cls):
        assert issubclass(pygmens_style_cls, pygments.style.Style)
        self.pygmens_style_cls = pygmens_style_cls
        self._token_to_attrs_dict = None

    def get_token_to_attributes_dict(self):
        def get_attributes(token):
            try:
                style = self.pygmens_style_cls.style_for_token(token)
                return Attrs(color=style['color'],
                             bgcolor=style['bgcolor'],
                             bold=style.get('bold', False),
                             underline=style.get('underline', False),
                             reverse=False)

            except KeyError:
                return _default_attrs

        if self._token_to_attrs_dict is None:
            self._token_to_attrs_dict = TokenToAttrsCache(get_attributes)

        return self._token_to_attrs_dict

    def invalidation_hash(self):
        return id(self.pygmens_style_cls)


class TokenToAttrsCache(dict):
    """
    A cache structure that maps Pygments Tokens to :class:`.Attr`.
    (This is an important speed up.)
    """
    def __init__(self, get_style_for_token):
        self.get_style_for_token = get_style_for_token

    def __missing__(self, token):
        try:
            result = self.get_style_for_token(token)
        except KeyError:
            result = None

        self[token] = result
        return result


default_style_extensions = {
    # Highlighting of search matches in document.
    Token.SearchMatch:                            '#000000 bg:#888888',
    Token.SearchMatch.Current:                    '#ffffff bg:#aa8888 underline',

    # Highlighting of select text in document.
    Token.SelectedText:                           '#ffffff bg:#666666',

    # Highlighting of matching brackets.
    Token.MatchingBracket:                        'bg:#aaaaff #000000',

    # Line numbers.
    Token.LineNumber:                             '#888888',
    Token.LineNumber.Current:                     'bold',

    # Default prompt.
    Token.Prompt:                                 'bold',
    Token.Prompt.Arg:                             'noinherit',
    Token.Prompt.Search:                          'noinherit',
    Token.Prompt.Search.Text:                     'bold',

    # Search toolbar.
    Token.Toolbar.Search:                         'bold',
    Token.Toolbar.Search.Text:                    'nobold',

    # System toolbar
    Token.Toolbar.System:                         'bold',

    # "arg" toolbar.
    Token.Toolbar.Arg:                            'bold',
    Token.Toolbar.Arg.Text:                       'nobold',

    # Validation toolbar.
    Token.Toolbar.Validation:                     'bg:#550000 #ffffff',

    # Completions toolbar.
    Token.Toolbar.Completions:                    'bg:#bbbbbb #000000',
    Token.Toolbar.Completions.Arrow:              'bg:#bbbbbb #000000 bold',
    Token.Toolbar.Completions.Completion:         'bg:#bbbbbb #000000',
    Token.Toolbar.Completions.Completion.Current: 'bg:#444444 #ffffff',

    # Completions menu.
    Token.Menu.Completions.Completion:            'bg:#bbbbbb #000000',
    Token.Menu.Completions.Completion.Current:    'bg:#888888 #ffffff',
    Token.Menu.Completions.Meta:                  'bg:#999999 #000000',
    Token.Menu.Completions.Meta.Current:          'bg:#aaaaaa #000000',
    Token.Menu.Completions.MultiColumnMeta:       'bg:#aaaaaa #000000',
    Token.Menu.Completions.ProgressBar:           'bg:#aaaaaa',
    Token.Menu.Completions.ProgressButton:        'bg:#000000',

    # Scrollbars.
    Token.Scrollbar:                              'bg:#444444',
    Token.Scrollbar.Button:                       'bg:#888888',
    Token.Scrollbar.Arrow:                        'bg:#222222 #ffffff',

    # Auto suggestion text.
    Token.AutoSuggestion:                         '#666666',

    # When Control-C has been pressed. Grayed.
    Token.Aborted:                                '#888888',
}


class DefaultStyle(pygments.styles.default.DefaultStyle):
    """
    Default Pygments style.
    """
    background_color = None
    styles = {}
    styles.update(default_style_extensions)
    styles.update(pygments.styles.default.DefaultStyle.styles)
