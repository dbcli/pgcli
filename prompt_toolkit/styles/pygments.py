"""
Adaptor for building prompt_toolkit styles, starting from a Pygments style.

Usage::

    from pygments.styles.tango import TangoStyle
    style = style_from_pygments(pygments_style_cls=TangoStyle)
"""
from __future__ import unicode_literals, absolute_import
from .style import Style

__all__ = (
    'style_from_pygments',
    'token_list_to_formatted_text',
)


def style_from_pygments(pygments_style_cls=None):
    """
    Shortcut to create a :class:`.Style` instance from a Pygments style class
    and a style dictionary.

    Example::

        from prompt_toolkit.styles.from_pygments import style_from_pygments
        from pygments.styles import get_style_by_name
        style = style_from_pygments(get_style_by_name('monokai'))

    :param pygments_style_cls: Pygments style class to start from.
    """
    # Import inline.
    from pygments.style import Style as pygments_Style
    assert issubclass(pygments_style_cls, pygments_Style)

    pygments_style = []

    if pygments_style_cls is not None:
        for token, style in pygments_style_cls.styles.items():
            pygments_style.append((_pygments_token_to_classname(token), style))

    return Style(pygments_style)


def _pygments_token_to_classname(token):
    """
    Turn e.g. `Token.Name.Exception` into `'pygments.name.exception'`.

    (Our Pygments lexer will also turn the tokens that pygments produces in a
    prompt_toolkit list of fragments that match these styling rules.)
    """
    return 'pygments.' + '.'.join(token).lower()


def token_list_to_formatted_text(token_list):
    """
    Turn a pygments token list into a list of prompt_toolkit text fragments
    (``(style_str, text)`` tuples).
    """
    result = []

    for token, text in token_list:
        result.append(('class:' + _pygments_token_to_classname(token), text))

    return result
