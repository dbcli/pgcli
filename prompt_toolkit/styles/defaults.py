"""
The default styling.
"""
from __future__ import unicode_literals
from prompt_toolkit.token import Token

__all__ = (
    'DEFAULT_STYLE_DICTIONARY',

    # Old names.
    'DEFAULT_STYLE_EXTENSIONS',
    'default_style_extensions',
)


#: Styling of prompt-toolkit specific tokens, that are not know by the default
#: Pygments style.
PROMPT_TOOLKIT_STYLE = {
    # Highlighting of search matches in document.
    Token.SearchMatch:                            'noinherit reverse',
    Token.SearchMatch.Current:                    'noinherit #ffffff bg:#448844 underline',

    # Highlighting of select text in document.
    Token.SelectedText:                           'reverse',

    Token.CursorColumn:                           'bg:#dddddd',
    Token.CursorLine:                             'underline',
    Token.ColorColumn:                            'bg:#ccaacc',

    # Highlighting of matching brackets.
    Token.MatchingBracket:                        '',
    Token.MatchingBracket.Other:                  '#000000 bg:#aacccc',
    Token.MatchingBracket.Cursor:                 '#ff8888 bg:#880000',

    Token.MultipleCursors.Cursor:                 '#000000 bg:#ccccaa',

    # Line numbers.
    Token.LineNumber:                             '#888888',
    Token.LineNumber.Current:                     'bold',
    Token.Tilde:                                  '#8888ff',

    # Default prompt.
    Token.Prompt:                                 '',
    Token.Prompt.Arg:                             'noinherit',
    Token.Prompt.Search:                          'noinherit',
    Token.Prompt.Search.Text:                     '',

    # Search toolbar.
    Token.Toolbar.Search:                         'bold',
    Token.Toolbar.Search.Text:                    'nobold',

    # System toolbar
    Token.Toolbar.System:                         'bold',
    Token.Toolbar.System.Text:                    'nobold',

    # "arg" toolbar.
    Token.Toolbar.Arg:                            'bold',
    Token.Toolbar.Arg.Text:                       'nobold',

    # Validation toolbar.
    Token.Toolbar.Validation:                     'bg:#550000 #ffffff',
    Token.WindowTooSmall:                         'bg:#550000 #ffffff',

    # Completions toolbar.
    Token.Toolbar.Completions:                    'bg:#bbbbbb #000000',
    Token.Toolbar.Completions.Arrow:              'bg:#bbbbbb #000000 bold',
    Token.Toolbar.Completions.Completion:         'bg:#bbbbbb #000000',
    Token.Toolbar.Completions.Completion.Current: 'bg:#444444 #ffffff',

    # Completions menu.
    Token.Menu.Completions:                       'bg:#bbbbbb #000000',
    Token.Menu.Completions.Completion:            '',
    Token.Menu.Completions.Completion.Current:    'bg:#888888 #ffffff',
    Token.Menu.Completions.Meta:                  'bg:#999999 #000000',
    Token.Menu.Completions.Meta.Current:          'bg:#aaaaaa #000000',
    Token.Menu.Completions.MultiColumnMeta:       'bg:#aaaaaa #000000',

    # Scrollbars.
    Token.Scrollbar.Background:                   '',
    Token.Scrollbar.Button:                       'bg:#888888',
    Token.Scrollbar.Start:                        'underline #ffffff',
    Token.Scrollbar.End:                          'underline #000000',
    Token.Scrollbar.Arrow:                        'noinherit bold',

    # Auto suggestion text.
    Token.AutoSuggestion:                         '#666666',

    # Trailing whitespace and tabs.
    Token.TrailingWhiteSpace:                     '#999999',
    Token.Tab:                                    '#999999',

    # When Control-C has been pressed. Grayed.
    Token.Aborted:                                '#888888',

    # Entering a Vi digraph.
    Token.Digraph:                                '#4444ff',
}


WIDGETS_STYLE = {
    # Buttons.
    Token.Button:                                 '',
    Token.Button.Arrow:                           'bold',
    Token.Button | Token.Focussed:                'bg:#880000 #ffffff',

    # Dialog windows.
    Token.Dialog:                                 'bg:#4444ff',
    Token.Dialog.Body:                            'bg:#ffffff #000000',
    Token.Dialog | Token.Frame.Label:             '#ff0000 bold',
    Token.Dialog.Body | Token.TextArea:            'bg:#cccccc',
    Token.Dialog.Body | Token.TextArea | Token.LastLine: 'underline',

    # Scrollbars in dialogs.
    Token.Dialog.Body | Token.Scrollbar.Background: '',
    Token.Dialog.Body | Token.Scrollbar.Button:     'bg:#000000',
    Token.Dialog.Body | Token.Scrollbar.Arrow:      '',
    Token.Dialog.Body | Token.Scrollbar.Start:      'nounderline',
    Token.Dialog.Body | Token.Scrollbar.End:        'nounderline',

    # Shadows.
    Token.Dialog | Token.Shadow:                  'bg:#000088',
    Token.Dialog.Body | Token.Shadow:             'bg:#aaaaaa',

    Token.ProgressBar:                            'bg:#000088 important',
    Token.ProgressBar.Used:                       'bg:#ff0000 important',
}


# The default Pygments style, include this by default in case a Pygments lexer
# is used.
PYGMENTS_DEFAULT_STYLE = {
    Token.Whitespace:                "#bbbbbb",
    Token.Comment:                   "italic #408080",
    Token.Comment.Preproc:           "noitalic #BC7A00",

    #Keyword:                   "bold #AA22FF",
    Token.Keyword:                   "bold #008000",
    Token.Keyword.Pseudo:            "nobold",
    Token.Keyword.Type:              "nobold #B00040",

    Token.Operator:                  "#666666",
    Token.Operator.Word:             "bold #AA22FF",

    Token.Name.Builtin:              "#008000",
    Token.Name.Function:             "#0000FF",
    Token.Name.Class:                "bold #0000FF",
    Token.Name.Namespace:            "bold #0000FF",
    Token.Name.Exception:            "bold #D2413A",
    Token.Name.Variable:             "#19177C",
    Token.Name.Constant:             "#880000",
    Token.Name.Label:                "#A0A000",
    Token.Name.Entity:               "bold #999999",
    Token.Name.Attribute:            "#7D9029",
    Token.Name.Tag:                  "bold #008000",
    Token.Name.Decorator:            "#AA22FF",

    Token.String:                    "#BA2121",
    Token.String.Doc:                "italic",
    Token.String.Interpol:           "bold #BB6688",
    Token.String.Escape:             "bold #BB6622",
    Token.String.Regex:              "#BB6688",
    #Token.String.Symbol:             "#B8860B",
    Token.String.Symbol:             "#19177C",
    Token.String.Other:              "#008000",
    Token.Number:                    "#666666",

    Token.Generic.Heading:           "bold #000080",
    Token.Generic.Subheading:        "bold #800080",
    Token.Generic.Deleted:           "#A00000",
    Token.Generic.Inserted:          "#00A000",
    Token.Generic.Error:             "#FF0000",
    Token.Generic.Emph:              "italic",
    Token.Generic.Strong:            "bold",
    Token.Generic.Prompt:            "bold #000080",
    Token.Generic.Output:            "#888",
    Token.Generic.Traceback:         "#04D",

    Token.Error:                     "border:#FF0000"
}


# Combine all styles in one dictionary.
DEFAULT_STYLE_DICTIONARY = {}
DEFAULT_STYLE_DICTIONARY.update(PROMPT_TOOLKIT_STYLE)
DEFAULT_STYLE_DICTIONARY.update(WIDGETS_STYLE)
DEFAULT_STYLE_DICTIONARY.update(PYGMENTS_DEFAULT_STYLE)


# Old names.
default_style_extensions = DEFAULT_STYLE_DICTIONARY
DEFAULT_STYLE_EXTENSIONS = DEFAULT_STYLE_DICTIONARY
