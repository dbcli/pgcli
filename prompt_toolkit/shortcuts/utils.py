from __future__ import unicode_literals
from prompt_toolkit.styles import default_style, BaseStyle
from prompt_toolkit.renderer import print_text_fragments as renderer_print_text_fragments
from prompt_toolkit.output.defaults import create_output

__all__ = (
    'print_text_fragments',
    'clear',
)


def print_text_fragments(text_fragments, style=None, true_color=False, file=None):
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
        print_text_fragments(fragments, style=style)

    If you want to print a list of Pygments tokens, use
    ``prompt_toolkit.style.token_list_to_text_fragments`` to do the conversion.

    :param text_fragments: List of ``(style_str, text)`` tuples.
    :param style: :class:`.Style` instance for the color scheme.
    :param true_color: When True, use 24bit colors instead of 256 colors.
    :param file: The output file. This can be `sys.stdout` or `sys.stderr`.
    """
    if style is None:
        style = default_style()
    assert isinstance(style, BaseStyle)

    output = create_output(true_color=true_color, stdout=file)
    renderer_print_text_fragments(output, text_fragments, style)


def clear():
    """
    Clear the screen.
    """
    out = create_output()
    out.erase_screen()
    out.cursor_goto(0, 0)
    out.flush()
