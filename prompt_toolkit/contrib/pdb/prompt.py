from __future__ import unicode_literals, absolute_import
from prompt_toolkit.layout.prompt import Prompt


class PdbPrompt(Prompt):
    """
    Pdb prompt.

    Show "(pdb)" when we have a pdb command or '>>>' when the user types a
    Python command.
    """
    def __init__(self, pdb_commands):
        super(PdbPrompt, self).__init__()
        self.pdb_commands = pdb_commands

    def tokens(self, cli):
        # Get the first word entered.
        command = cli.line.document.text.lstrip()
        if command:
            command = command.split()[0]

        if any(c.startswith(command) for c in self.pdb_commands):
            return [(self.token, '(pdb) ')]
        else:
            return [(self.token, '  >>> ')]
