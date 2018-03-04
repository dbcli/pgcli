from pygments.token import string_to_tokentype
from pygments.util import ClassNotFound
from prompt_toolkit.styles import PygmentsStyle
import pygments.styles

from pygments.style import Style

def style_factory(name, cli_style):
    try:
        style = pygments.styles.get_style_by_name(name)
    except ClassNotFound:
        style = pygments.styles.get_style_by_name('native')

    custom_styles = {}
    for token in cli_style:
        try:
            custom_styles[string_to_tokentype(
                token)] = style.styles[string_to_tokentype(cli_style[token])]
        except AttributeError as err:
            custom_styles[string_to_tokentype(token)] = cli_style[token]

    return PygmentsStyle.from_defaults(style_dict=custom_styles,
                                       pygments_style_cls=style)


def style_factory_output(name, cli_style):
    try:
        style = pygments.styles.get_style_by_name(name).styles
    except ClassNotFound:
        style = pygments.styles.get_style_by_name('native').styles

    for token in cli_style:
        try:
            style.update({string_to_tokentype(
                token): style[string_to_tokentype(cli_style[token])], })
        except AttributeError as err:
            style.update(
                {string_to_tokentype(token): cli_style[token], })

    class OutputStyle(pygments.style.Style):
        default_style = ""
        styles = style

    return OutputStyle
