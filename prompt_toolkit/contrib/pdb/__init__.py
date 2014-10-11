#!/usr/bin/env python
"""
Python debugger prompt.
Enhanced version of Pdb, using a prompt-toolkit front-end.

Usage::

    from prompt_toolkit.contrib.pdb import set_trace
    set_trace()
"""
from __future__ import unicode_literals, absolute_import
from pygments.lexers import PythonLexer
from pygments.token import Token

from prompt_toolkit import CommandLineInterface, AbortAction, Exit

from prompt_toolkit.contrib.python_input import PythonCompleter, PythonValidator
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter
from prompt_toolkit.contrib.regular_languages.lexer import GrammarLexer
from prompt_toolkit.contrib.regular_languages.validation import GrammarValidator
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_bindings.emacs import emacs_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.toolbars import SystemToolbar, ValidationToolbar, ArgToolbar, SearchToolbar
from prompt_toolkit.line import Line

from .commands import commands_with_help, shortcuts
from .completers import PythonFileCompleter, PythonFunctionCompleter, BreakPointListCompleter, AliasCompleter, PdbCommandsCompleter
from .completion_hints import CompletionHint
from .grammar import create_pdb_grammar
from .key_bindings import custom_pdb_key_bindings
from .prompt import PdbPrompt
from .style import PdbStyle
from .toolbars import SourceCodeToolbar, ShortcutsToolbar, PdbStatusToolbar

import os
import pdb
import sys
import weakref


__all__ = (
    'PtPdb',
    'set_trace',
)


class PtPdb(pdb.Pdb):
    def __init__(self):
        pdb.Pdb.__init__(self)

        # Cache for the grammar.
        self._grammar_cache = None  # (current_pdb_commands, grammar) tuple.

        self._cli_history = FileHistory(os.path.expanduser('~/.ptpdb_history'))

    def cmdloop(self, intro=None):
        """
        Copy/Paste of pdb.Pdb.cmdloop. But using our own CommandLineInterface
        for reading input instead.
        """
        self.preloop()

        if intro is not None:
            self.intro = intro
        if self.intro:
            self.stdout.write(str(self.intro)+"\n")
        stop = None
        while not stop:
            if self.cmdqueue:
                line = self.cmdqueue.pop(0)
            else:
                if self.use_rawinput:
                    line = self._get_input()

            line = self.precmd(line)
            stop = self.onecmd(line)
            stop = self.postcmd(stop, line)
        self.postloop()

    def _get_current_pdb_commands(self):
        return (
            list(commands_with_help.keys()) +
            list(shortcuts.keys()) +
            list(self.aliases.keys()))

    def _create_grammar(self):
        """
        Return the compiled grammar for this PDB shell.

        The grammar of PDB depends on the available list of PDB commands (which
        depends on the currently defined aliases.) Therefor we generate a new
        grammar when it changes, but cache it otherwise. (It's still expensive
        to compile.)
        """
        pdb_commands = self._get_current_pdb_commands()

        if self._grammar_cache is None or self._grammar_cache[0] != pdb_commands:
            self._grammar_cache = [
                pdb_commands,
                create_pdb_grammar(pdb_commands)]

        return self._grammar_cache[1]

    def _get_input(self):
        """
        Read PDB input. Return input text.
        """
        g = self._create_grammar()

        cli = CommandLineInterface(
            layout=Layout(
                before_input=PdbPrompt(self._get_current_pdb_commands()),
                show_tildes=True,
                min_height=15,
                lexer=GrammarLexer(
                    g,
                    tokens={'pdb_command': Token.PdbCommand},
                    lexers={'python_code': PythonLexer}
                ),
                after_input=CompletionHint(),
                menus=[CompletionsMenu()],
                top_toolbars=[],
                bottom_toolbars=[
                    SystemToolbar(),
                    ArgToolbar(),
                    SearchToolbar(),
                    SourceCodeToolbar(weakref.ref(self)),
                    ValidationToolbar(),
                    ShortcutsToolbar(),
                    PdbStatusToolbar(weakref.ref(self)),
                ]),
            line=Line(
                completer=GrammarCompleter(g, completers={
                    'enabled_breakpoint': BreakPointListCompleter(only_enabled=True),
                    'disabled_breakpoint': BreakPointListCompleter(only_disabled=True),
                    'alias_name': AliasCompleter(self),
                    'python_code': PythonCompleter(lambda: self.curframe.f_globals, lambda: self.curframe.f_locals),
                    'breakpoint': BreakPointListCompleter(),
                    'pdb_command': PdbCommandsCompleter(self),
                    'python_file': PythonFileCompleter(),
                    'python_function': PythonFunctionCompleter(self),
                }),
                history=self._cli_history,
                validator=GrammarValidator(g, {
                    'python_code': PythonValidator()
                }),
            ),
            key_binding_factories=[emacs_bindings, custom_pdb_key_bindings],
            style=PdbStyle)

        try:
            return cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION).text
        except Exit:
            # Turn Control-D key press into a 'quit' command.
            return 'q'


def set_trace():
    PtPdb().set_trace(sys._getframe().f_back)
