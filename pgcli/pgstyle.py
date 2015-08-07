from pygments.token import Token
from pygments.style import Style
from pygments.util import ClassNotFound
from prompt_toolkit.styles import default_style_extensions
import pygments.styles


def style_factory(name, cli_style):
    try:
        style = pygments.styles.get_style_by_name(name)
    except ClassNotFound:
        style = pygments.styles.get_style_by_name('native')

    class PGStyle(Style):
        styles = {}

        styles.update(style.styles)
        styles.update(default_style_extensions)
        custom_styles = dict([(eval(x), y) for x, y in cli_style.items()])
        styles.update(custom_styles)
    return PGStyle
