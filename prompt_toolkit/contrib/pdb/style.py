from __future__ import unicode_literals
from prompt_toolkit.contrib.python_input import PythonStyle
from pygments.token import Token


class PdbStyle(PythonStyle):
    styles = {
        # Pdb tokens.
        Token.Prompt.BeforeInput:                      'bold #008800',
        Token.PdbCommand:                              'bold',
        Token.CompletionHint.Symbol:                   '#9a8888',
        Token.CompletionHint.Parameter:                '#ba4444 bold',
        Token.Toolbar.Status.Pdb.Filename:             'bg:#222222 #aaaaaa',
        Token.Toolbar.Status.Pdb.Lineno:               'bg:#222222 #ffffff',
        Token.Toolbar.Status.Pdb.Shortcut.Key:         'bg:#222222 #aaaaaa',
        Token.Toolbar.Status.Pdb.Shortcut.Description: 'bg:#222222 #aaaaaa',
    }
    styles.update(PythonStyle.styles)
