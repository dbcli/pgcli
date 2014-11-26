from pygments.token import Token
from pygments.style import Style
from pygments.styles.default import DefaultStyle

class PGStyle(Style):
    styles = {
            Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
            Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
            Token.Menu.Completions.ProgressButton: 'bg:#003333',
            Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
            Token.SelectedText: '#ffffff bg:#6666aa',
            Token.IncrementalSearchMatch: '#ffffff bg:#4444aa',
            Token.IncrementalSearchMatch.Current: '#ffffff bg:#44aa44',
            }
    styles.update(DefaultStyle.styles)
