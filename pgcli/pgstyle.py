from pygments.token import string_to_tokentype
from pygments.util import ClassNotFound
from prompt_toolkit.styles import PygmentsStyle
import pygments.styles


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
