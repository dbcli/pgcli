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


class ShortcutsToolbar(Toolbar):
    """
    Display shortcuts.
    """
    def get_tokens(self, cli, width):
        result = []
        append = result.append
        TB = Token.X.Shortcut

        append((TB, '    '))
        append((TB.Key, '[F6]'))
        append((TB.Description, ' Open Repl '))
        append((TB.Key, '[F7]'))
        append((TB.Description, ' Step  '))
        append((TB.Key, '[F8]'))
        append((TB.Description, ' Next  '))
        append((TB.Key, '[F9]'))
        append((TB.Description, ' Continue '))

        return result


class PdbStatusToolbar(Toolbar):
    """
    Toolbar which shows the Pdb status. (current line and line number.)
    """
    def __init__(self, pdb_ref, token=None):
        self._pdb_ref = pdb_ref
        token = token or Token.Toolbar.Status
        super(PdbStatusToolbar, self).__init__(token=token)

    def get_tokens(self, cli, width):
        result = []
        append = result.append
        TB = self.token
        pdb = self._pdb_ref()

        # Show current input mode.
        result.extend(get_inputmode_tokens(self.token, False, cli))

        # Filename and line number.
        append((TB, ' Break at: '))
        append((TB.Pdb.Filename, pdb.curframe.f_code.co_filename or 'None'))
        append((TB, ' '))
        append((TB.Pdb.Lineno, ': %s' % pdb.curframe.f_lineno))

        # Python version
        version = sys.version_info
        append((TB, ' - '))
        append((TB.PythonVersion, '%s %i.%i.%i' % (platform.python_implementation(),
               version[0], version[1], version[2])))

        return result
