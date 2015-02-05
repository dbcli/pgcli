from pygments.token import Token
from pygments.style import Style
from pygments.util import ClassNotFound
import pygments.styles


def style_factory(name):
    try:
        style = pygments.styles.get_style_by_name(name)
    except ClassNotFound:
        style = pygments.styles.get_style_by_name('native')

    class PGStyle(Style):
        styles = {
                Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
                Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
                Token.Menu.Completions.ProgressButton: 'bg:#003333',
                Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
                Token.SelectedText: '#ffffff bg:#6666aa',
                Token.IncrementalSearchMatch: '#ffffff bg:#4444aa',
                Token.IncrementalSearchMatch.Current: '#ffffff bg:#44aa44',
                Token.Toolbar: 'bg:#440044 #ffffff',
                Token.Toolbar.Status: 'bg:#222222 #aaaaaa',
                Token.Toolbar.Status.Off: 'bg:#222222 #888888',
                Token.Toolbar.Status.On: 'bg:#222222 #ffffff',
                }
        styles.update(style.styles)

    return PGStyle
