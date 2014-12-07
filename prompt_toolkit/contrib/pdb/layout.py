from __future__ import unicode_literals, absolute_import

from prompt_toolkit.layout.margins import LeftMarginWithLineNumbers
from pygments.token import Token


class PdbLeftMargin(LeftMarginWithLineNumbers):
    """
    Pdb prompt.

    Show "(pdb)" when we have a pdb command or '>>>' when the user types a
    Python command.
    """
    def __init__(self, pdb_commands):
        super(PdbLeftMargin, self).__init__()
        self.pdb_commands = pdb_commands

    def width(self, cli):
        return 6

    def write(self, cli, screen, y, line_number):
        if y == 0:
            screen.write_highlighted(self._first_line(cli))
        else:
            super(PdbLeftMargin, self).write(cli, screen, y, line_number)

    def _first_line(self, cli):
        # Get the first word entered.
        command = cli.buffers['default'].document.text.lstrip()
        if command:
            command = command.split()[0]

        if any(c.startswith(command) for c in self.pdb_commands):
            return [(Token.Prompt, '(pdb) ')]
        else:
            return [(Token.Prompt, '  >>> ')]
