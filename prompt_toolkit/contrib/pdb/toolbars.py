from __future__ import unicode_literals, absolute_import
from pygments.lexers import PythonLexer
from pygments.token import Token

from prompt_toolkit.contrib.python_input import get_inputmode_tokens
from prompt_toolkit.layout.toolbars import TextToolbar
from prompt_toolkit.layout.toolbars import Toolbar

import linecache
import platform
import sys


class SourceCodeToolbar(TextToolbar):
    def __init__(self, pdb_ref):
        super(SourceCodeToolbar, self).__init__(
            lexer=PythonLexer,
            height=7,
            text=self._get_source_code(pdb_ref))

    def _get_source_code(self, pdb_ref):
        """
        Return source code around current line as string.
        (Partly taken from Pdb.do_list.)
        """
        pdb = pdb_ref()

        filename = pdb.curframe.f_code.co_filename
        breaklist = pdb.get_file_breaks(filename)

        first = max(1,  pdb.curframe.f_lineno - 3)
        last = first + 6

        result = []

        for lineno in range(first, last+1):
            line = linecache.getline(filename, lineno, pdb.curframe.f_globals)
            if not line:
                line = '[EOF]'
                break
            else:
                s = repr(lineno).rjust(3)
                if len(s) < 4:
                    s = s + ' '
                if lineno in breaklist:
                    s = s + 'B'
                else:
                    s = s + ' '
                if lineno == pdb.curframe.f_lineno:
                    s = s + '->'
                else:
                    s = s + '  '

                result.append(s + ' ' + line)

        return ''.join(result)


class PdbStatusToolbar(Toolbar):
    """
    Toolbar which shows the Pdb status. (current line and line number.)
    """
    def __init__(self, pdb_ref, key_bindings_manager, token=None):
        self._pdb_ref = pdb_ref
        self.key_bindings_manager = key_bindings_manager
        token = token or Token.Toolbar.Status
        super(PdbStatusToolbar, self).__init__(token=token)

    def get_tokens(self, cli, width):
        result = []
        append = result.append
        TB = self.token
        pdb = self._pdb_ref()

        # Shortcuts
        append((TB.Pdb.Shortcut.Key, ' [F8]'))
        append((TB.Pdb.Shortcut.Description, ' Step '))
        append((TB.Pdb.Shortcut.Key, '[F9]'))
        append((TB.Pdb.Shortcut.Description, ' Next '))
        append((TB.Pdb.Shortcut.Key, '[F10]'))
        append((TB.Pdb.Shortcut.Description, ' Continue'))

        # Filename and line number.
        append((TB, ' | At: '))
        append((TB.Pdb.Filename, pdb.curframe.f_code.co_filename or 'None'))
        append((TB.Pdb.Lineno, ':%s' % pdb.curframe.f_lineno))

        return result
