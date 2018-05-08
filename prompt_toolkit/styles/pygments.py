"""
Adaptor for building prompt_toolkit styles, starting from a Pygments style.

Usage::

    from pygments.styles.tango import TangoStyle
    style = style_from_pygments_cls(pygments_style_cls=TangoStyle)
"""
from __future__ import unicode_literals, absolute_import
from .style import Style

__all__ = [
    'style_from_pygments_cls',
    'style_from_pygments_dict',
    'pygments_token_to_classname',
]


def style_from_pygments_cls(pygments_style_cls):
    """
    Shortcut to create a :class:`.Style` instance from a Pygments style class
    and a style dictionary.

    Example::

        from prompt_toolkit.styles.from_pygments import style_from_pygments_cls
        from pygments.styles import get_style_by_name
        style = style_from_pygments_cls(get_style_by_name('monokai'))

    :param pygments_style_cls: Pygments style class to start from.
    """
    # Import inline.
    from pygments.style import Style as pygments_Style
    assert issubclass(pygments_style_cls, pygments_Style)

    return style_from_pygments_dict(pygments_style_cls.styles)


def style_from_pygments_dict(pygments_dict):
    """
    Create a :class:`.Style` instance from a Pygments style dictionary.
    (One that maps Token objects to style strings.)
    """
    assert hasattr(pygments_dict, 'items')  # collections.abc.Mapping only available on Python 3.
    pygments_style = []

    for token, style in pygments_dict.items():
        pygments_style.append((pygments_token_to_classname(token), style))

    return Style(pygments_style)


def pygments_token_to_classname(token):
    """
    Turn e.g. `Token.Name.Exception` into `'pygments.name.exception'`.

    (Our Pygments lexer will also turn the tokens that pygments produces in a
    prompt_toolkit list of fragments that match these styling rules.)
    """
    parts = ('pygments', ) + token
    return '.'.join(parts).lower()
