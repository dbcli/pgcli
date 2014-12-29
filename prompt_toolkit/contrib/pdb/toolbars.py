from __future__ import unicode_literals, absolute_import
from pygments.token import Token

from prompt_toolkit.layout.toolbars import TokenListToolbar
from prompt_toolkit.layout.screen import Char

from prompt_toolkit.filters import IsDone


class PdbShortcutsToolbar(TokenListToolbar):
    """
    Toolbar which shows the Pdb status. (current line and line number.)
    """
    def __init__(self, pdb_ref):
        token = Token.Toolbar.Shortcuts

        def get_tokens(cli):
            return [
                (token.Key, ' [F8]'),
                (token.Description, ' Step '),
                (token.Key, '[F9]'),
                (token.Description, ' Next '),
                (token.Key, '[F10]'),
                (token.Description, ' Continue'),
            ]

        super(PdbShortcutsToolbar, self).__init__(get_tokens,
                                               default_char=Char(token=token),
                                               filter=~IsDone())


class FileLocationToolbar(TokenListToolbar):
    """
    Toolbar which shows the filename and line number.
    """
    def __init__(self, pdb_ref):
        token = Token.Toolbar.Location

        def get_tokens(cli):
            pdb = pdb_ref()

            return [
                (token, 'At: '),
                (token.Filename, pdb.curframe.f_code.co_filename or 'None'),
                (token.Lineno, ':%s' % pdb.curframe.f_lineno),
            ]

        super(FileLocationToolbar, self).__init__(get_tokens,
                                                  default_char=Char(token=token),
                                                  filter=~IsDone())
