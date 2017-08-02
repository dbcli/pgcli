from __future__ import unicode_literals, print_function
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.output.base import Output
from prompt_toolkit.output.defaults import create_output, get_default_output
from prompt_toolkit.renderer import print_formatted_text as renderer_print_formatted_text
from prompt_toolkit.styles import default_style, BaseStyle
import six

__all__ = (
    'print',
    'clear',
    'set_title',
    'clear_title',
)

def print(*values, **kwargs):
    """
    ::
        print(*values, sep=' ', end='\n', file=None, flush=False, style=None, output=None)

    Print a list of (style_str, text) tuples in the given style to the output.
    E.g.::

        style = Style.from_dict({
            'hello': '#ff0066',
            'world': '#884444 italic',
        })
        fragments = [
            ('class:hello', 'Hello'),
            ('class:world', 'World'),
        ]
        print(fragments, style=style)

    If you want to print a list of Pygments tokens, use
    ``prompt_toolkit.style.token_list_to_formatted_text`` to do the conversion.

    :param values: A formatted string. This can be a list of
        ``(style_str, text)`` tuples.
    :param sep: String inserted between values, default a space.
    :param end: String appended after the last value, default a newline.
    :param style: :class:`.Style` instance for the color scheme.
    """
    # Pop kwargs (Python 2 compatibility).
    sep = kwargs.pop('sep', ' ')
    end = kwargs.pop('end', '\n')
    file = kwargs.pop('file', None)
    flush = kwargs.pop('flush', False)
    style = kwargs.pop('style', None)
    output = kwargs.pop('output', None)
    assert not kwargs
    assert not (output and file)

    # Other defaults.
    if style is None:
        style = default_style()

    if output is None:
        if file:
            output = create_output(stdout=file)
        else:
            output = get_default_output()

    assert isinstance(style, BaseStyle)
    assert isinstance(output, Output)

    # Merges values.
    def to_text(val):
        return to_formatted_text(val, auto_convert=True)

    fragments = []
    for i, value in enumerate(values):
        fragments.extend(to_text(value))

        if sep and i != len(values) - 1:
            fragments.extend(to_text(sep))

    fragments.extend(to_text(end))

    # Print output.
    renderer_print_formatted_text(output, fragments, style)

    # Flush the output stream.
    if flush:
        output.flush()


def clear():
    """
    Clear the screen.
    """
    out = get_default_output()
    out.erase_screen()
    out.cursor_goto(0, 0)
    out.flush()


def set_title(text):
    """
    Set the terminal title.
    """
    assert isinstance(text, six.text_type)

    output = get_default_output()
    output.set_title(text)


def clear_title():
    """
    Erase the current title.
    """
    set_title('')
