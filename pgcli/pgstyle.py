from pygments.token import string_to_tokentype
from pygments.util import ClassNotFound
from prompt_toolkit.styles import PygmentsStyle
import pygments.styles


def style_factory(name, cli_style):
    try:
        style = pygments.styles.get_style_by_name(name)
    except ClassNotFound:
        style = pygments.styles.get_style_by_name('native')

    custom_styles = dict([(string_to_tokentype(x), y)
                            for x, y in cli_style.items()])

    return PygmentsStyle.from_defaults(style_dict=custom_styles,
                                       pygments_style_cls=style)
