"""
The base classes for the styling.
"""
from __future__ import unicode_literals, absolute_import
from abc import ABCMeta, abstractmethod, abstractproperty
from collections import namedtuple
from six import with_metaclass

__all__ = [
    'Attrs',
    'DEFAULT_ATTRS',
    'ANSI_COLOR_NAMES',
    'ANSI_COLOR_NAMES_ALIASES',
    'BaseStyle',
    'DummyStyle',
    'DynamicStyle',
]


#: Style attributes.
Attrs = namedtuple('Attrs', 'color bgcolor bold underline italic blink reverse hidden')
"""
:param color: Hexadecimal string. E.g. '000000' or Ansi color name: e.g. 'ansiblue'
:param bgcolor: Hexadecimal string. E.g. 'ffffff' or Ansi color name: e.g. 'ansired'
:param bold: Boolean
:param underline: Boolean
:param italic: Boolean
:param blink: Boolean
:param reverse: Boolean
:param hidden: Boolean
"""

#: The default `Attrs`.
DEFAULT_ATTRS = Attrs(color='', bgcolor='', bold=False, underline=False,
                      italic=False, blink=False, reverse=False, hidden=False)


#: ``Attrs.bgcolor/fgcolor`` can be in either 'ffffff' format, or can be any of
#: the following in case we want to take colors from the 8/16 color palette.
#: Usually, in that case, the terminal application allows to configure the RGB
#: values for these names.
#: ISO 6429 colors
ANSI_COLOR_NAMES = [
    'ansidefault',

    # Low intensity, dark.  (One or two components 0x80, the other 0x00.)
    'ansiblack', 'ansired', 'ansigreen', 'ansiyellow', 'ansiblue',
    'ansimagenta', 'ansicyan', 'ansigray',

    # High intensity, bright. (One or two components 0xff, the other 0x00. Not supported everywhere.)
    'ansibrightblack', 'ansibrightred', 'ansibrightgreen', 'ansibrightyellow',
    'ansibrightblue', 'ansibrightmagenta', 'ansibrightcyan', 'ansiwhite',
]


# People don't use the same ANSI color names everywhere. In prompt_toolkit 1.0
# we used some unconvential names (which were contributed like that to
# Pygments). This is fixed now, but we still support the old names.

# The table below maps the old aliases to the current names.
ANSI_COLOR_NAMES_ALIASES = {
    'ansidarkgray': 'ansibrightblack',
    'ansiteal': 'ansicyan',
    'ansiturquoise': 'ansibrightcyan',
    'ansibrown': 'ansiyellow',
    'ansipurple': 'ansimagenta',
    'ansifuchsia': 'ansibrightmagenta',
    'ansilightgray': 'ansigray',
    'ansidarkred': 'ansired',
    'ansidarkgreen': 'ansigreen',
    'ansidarkblue': 'ansiblue',
}
assert set(ANSI_COLOR_NAMES_ALIASES.values()).issubset(set(ANSI_COLOR_NAMES))
assert not (set(ANSI_COLOR_NAMES_ALIASES.keys()) & set(ANSI_COLOR_NAMES))


class BaseStyle(with_metaclass(ABCMeta, object)):
    """
    Abstract base class for prompt_toolkit styles.
    """
    @abstractmethod
    def get_attrs_for_style_str(self, style_str, default=DEFAULT_ATTRS):
        """
        Return :class:`.Attrs` for the given style string.

        :param style_str: The style string. This can contain inline styling as
            well as classnames (e.g. "class:title").
        :param default: `Attrs` to be used if no styling was defined.
        """

    @abstractproperty
    def style_rules(self):
        """
        The list of style rules, used to create this style.
        (Required for `DynamicStyle` and `_MergedStyle` to work.)
        """
        return []

    @abstractmethod
    def invalidation_hash(self):
        """
        Invalidation hash for the style. When this changes over time, the
        renderer knows that something in the style changed, and that everything
        has to be redrawn.
        """


class DummyStyle(BaseStyle):
    """
    A style that doesn't style anything.
    """
    def get_attrs_for_style_str(self, style_str, default=DEFAULT_ATTRS):
        return default

    def invalidation_hash(self):
        return 1  # Always the same value.

    @property
    def style_rules(self):
        return []


class DynamicStyle(BaseStyle):
    """
    Style class that can dynamically returns an other Style.

    :param get_style: Callable that returns a :class:`.Style` instance.
    """
    def __init__(self, get_style):
        self.get_style = get_style
        self._dummy = DummyStyle()

    def get_attrs_for_style_str(self, style_str, default=DEFAULT_ATTRS):
        style = self.get_style() or self._dummy

        assert isinstance(style, BaseStyle)
        return style.get_attrs_for_style_str(style_str, default)

    def invalidation_hash(self):
        return (self.get_style() or self._dummy).invalidation_hash()

    @property
    def style_rules(self):
        return (self.get_style() or self._dummy).style_rules
