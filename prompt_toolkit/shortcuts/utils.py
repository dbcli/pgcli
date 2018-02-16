from __future__ import unicode_literals, print_function
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.output import Output, ColorDepth
from prompt_toolkit.output.defaults import create_output, get_default_output
from prompt_toolkit.renderer import print_formatted_text as renderer_print_formatted_text
from prompt_toolkit.styles import default_ui_style, default_pygments_style, BaseStyle, merge_styles
import six

__all__ = [
    'print_formatted_text',
    'clear',
    'set_title',
    'clear_title',
]


def print_formatted_text(*values, **kwargs):
    """
    ::

        print_formatted_text(*values, sep=' ', end='\\n', file=None, flush=False, style=None, output=None)

    Print text to stdout. This is supposed to be compatible with Python's print
    function, but supports printing of formatted text. You can pass a
    :class:`~prompt_toolkit.formatted_text.FormattedText`,
    :class:`~prompt_toolkit.formatted_text.HTML` or
    :class:`~prompt_toolkit.formatted_text.ANSI` object to print formatted
    text.

    * Print HTML as follows::

        print_formatted_text(HTML('<i>Some italic text</i> <ansired>This is red!</ansired>'))

        style = Style.from_dict({
            'hello': '#ff0066',
            'world': '#884444 italic',
        })
        print_formatted_text(HTML('<hello>Hello</hello> <world>world</world>!'), style=style)

    * Print a list of (style_str, text) tuples in the given style to the
      output.  E.g.::

        style = Style.from_dict({
            'hello': '#ff0066',
            'world': '#884444 italic',
        })
        fragments = FormattedText([
            ('class:hello', 'Hello'),
            ('class:world', 'World'),
        ])
        print_formatted_text(fragments, style=style)

    If you want to print a list of Pygments tokens, wrap it in
    :class:`~prompt_toolkit.formatted_text.PygmentsTokens` to do the
    conversion.

    :param values: Any kind of printable object, or formatted string.
    :param sep: String inserted between values, default a space.
    :param end: String appended after the last value, default a newline.
    :param style: :class:`.Style` instance for the color scheme.
    :param include_default_pygments_style: `bool`. Include the default Pygments
        style when set to `True` (the default).
    """
    # Pop kwargs (Python 2 compatibility).
    sep = kwargs.pop('sep', ' ')
    end = kwargs.pop('end', '\n')
    file = kwargs.pop('file', None)
    flush = kwargs.pop('flush', False)
    style = kwargs.pop('style', None)
    output = kwargs.pop('output', None)
    color_depth = kwargs.pop('color_depth', None)
    include_default_pygments_style = kwargs.pop('include_default_pygments_style', True)
    assert not kwargs
    assert not (output and file)
    assert style is None or isinstance(style, BaseStyle)

    # Build/merge style.
    styles = [default_ui_style()]
    if include_default_pygments_style:
        styles.append(default_pygments_style())
    if style:
        styles.append(style)

    merged_style = merge_styles(styles)

    # Create Output object.
    if output is None:
        if file:
            output = create_output(stdout=file)
        else:
            output = get_default_output()

    assert isinstance(output, Output)

    # Get color depth.
    color_depth = color_depth or ColorDepth.default()

    # Merges values.
    def to_text(val):
        if isinstance(val, list):
            return to_formatted_text('{0}'.format(val))
        return to_formatted_text(val, auto_convert=True)

    fragments = []
    for i, value in enumerate(values):
        fragments.extend(to_text(value))

        if sep and i != len(values) - 1:
            fragments.extend(to_text(sep))

    fragments.extend(to_text(end))

    # Print output.
    renderer_print_formatted_text(
        output, fragments, merged_style, color_depth=color_depth)

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
