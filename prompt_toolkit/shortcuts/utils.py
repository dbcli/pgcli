from __future__ import unicode_literals
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.renderer import print_formatted_text as renderer_print_formatted_text
from prompt_toolkit.styles import default_style, BaseStyle
import six

__all__ = (
    'print_formatted_text',
    'clear',
    'set_title',
    'clear_title',
)


def print_formatted_text(formatted_text, style=None, true_color=False, file=None):
    """
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
        print_formatted_text(fragments, style=style)

    If you want to print a list of Pygments tokens, use
    ``prompt_toolkit.style.token_list_to_formatted_text`` to do the conversion.

    :param text_fragments: List of ``(style_str, text)`` tuples.
    :param style: :class:`.Style` instance for the color scheme.
    :param true_color: When True, use 24bit colors instead of 256 colors.
    :param file: The output file. This can be `sys.stdout` or `sys.stderr`.
    """
    if style is None:
        style = default_style()
    assert isinstance(style, BaseStyle)

    output = create_output(true_color=true_color, stdout=file)
    renderer_print_formatted_text(output, formatted_text, style)


def clear():
    """
    Clear the screen.
    """
    out = create_output()
    out.erase_screen()
    out.cursor_goto(0, 0)
    out.flush()


def set_title(text):
    """
    Set the terminal title.
    """
    assert isinstance(text, six.text_type)

    output = create_output()
    output.set_title(text)


def clear_title():
    """
    Erase the current title.
    """
    set_title('')
