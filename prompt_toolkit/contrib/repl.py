"""
Utility for creating a Python repl.

::

    from prompt_toolkit.contrib.repl import embed
    embed(globals(), locals(), vi_mode=False)

"""
# Warning: don't import `print_function` from __future__, otherwise we will
#          also get the print_function inside `eval` on Python 2.7.

from __future__ import unicode_literals

from pygments import highlight
from pygments.formatters.terminal256  import Terminal256Formatter
from pygments.lexers import PythonTracebackLexer

from prompt_toolkit import AbortAction, Exit
from prompt_toolkit.contrib.python_input import PythonCommandLineInterface, PythonStyle, AutoCompletionStyle

from six import exec_

import sys
import os
import traceback


__all__ = ('PythonRepl', 'embed')


class PythonRepl(PythonCommandLineInterface):
    def start_repl(self, startup_path=None):
        """
        Start the Read-Eval-Print Loop.
        """
        self._execute_startup(startup_path)

        # Run REPL loop until Exit.
        try:
            while True:
                # Read
                document = self.read_input(
                                on_abort=AbortAction.RETRY,
                                on_exit=AbortAction.RAISE_EXCEPTION)
                line = document.text

                if line and not line.isspace():
                    try:
                        # Eval and print.
                        self._execute(line)
                    except KeyboardInterrupt as e: # KeyboardInterrupt doesn't inherit from Exception.
                        self._handle_keyboard_interrupt(e)
                    except Exception as e:
                        self._handle_exception(e)

                    self.current_statement_index += 1
        except Exit:
            pass

    def _execute_startup(self, startup_path):
        """
        Load and execute startup file.
        """
        if startup_path:
            with open(startup_path, 'r') as f:
                code = compile(f.read(), startup_path, 'exec')
                exec_(code, self.globals, self.locals)

    def _execute(self, line):
        """
        Evaluate the line and print the result.
        """
        if line[0:1] == '!':
            # Run as shell command
            os.system(line[1:])
        else:
            # Try eval first
            try:
                result = eval(line, self.globals, self.locals)
                self.locals['_'] = self.locals['_%i' % self.current_statement_index] = result

                if result is not None:
                    try:
                        self.stdout.write('Out[%i]: %r\n' % (self.current_statement_index, result))
                    except UnicodeDecodeError:
                        # In Python 2: `__repr__` should return a bytestring,
                        # so to put it in a unicode context could raise an
                        # exception that the 'ascii' codec can't decode certain
                        # characters. Decode as utf-8 in that case.
                        self.stdout.write('Out[%i]: %s\n' % (self.current_statement_index, repr(result).decode('utf-8')))

            # If not a valid `eval` expression, run using `exec` instead.
            except SyntaxError:
                exec_(line, self.globals, self.locals)

            self.stdout.write('\n')
            self.stdout.flush()

    def _handle_exception(self, e):
        # Instead of just calling ``traceback.format_exc``, we take the
        # traceback and skip the bottom calls of this framework.
        t, v, tb = sys.exc_info()
        tblist = traceback.extract_tb(tb)[3:]
        l = traceback.format_list(tblist)
        if l:
            l.insert(0, "Traceback (most recent call last):\n")
        l.extend(traceback.format_exception_only(t, v))
        tb = ''.join(l)

        # Format exception and write to output.
        self.stdout.write(highlight(tb, PythonTracebackLexer(), Terminal256Formatter()))
        self.stdout.write('%s\n\n' % e)
        self.stdout.flush()

    def _handle_keyboard_interrupt(self, e):
        self.stdout.write('\rKeyboardInterrupt\n\n')
        self.stdout.flush()


def embed(globals=None, locals=None, vi_mode=False, history_filename=None, no_colors=False,
                autocompletion_style=AutoCompletionStyle.POPUP_MENU,
                startup_path=None):
    """
    Call this to embed  Python shell at the current point in your program.
    It's similar to `IPython.embed` and `bpython.embed`. ::

        from prompt_toolkit.contrib.repl import embed
        embed(globals(), locals(), vi_mode=False)

    :param vi_mode: Boolean. Use Vi instead of Emacs key bindings.
    """
    cli = PythonRepl(globals, locals, vi_mode=vi_mode, history_filename=history_filename,
            style=(None if no_colors else PythonStyle),
            autocompletion_style=autocompletion_style)
    cli.start_repl(startup_path=startup_path)
