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
from pygments.formatters.terminal256 import Terminal256Formatter
from pygments.lexers import PythonTracebackLexer

from prompt_toolkit import AbortAction, Exit
from prompt_toolkit.contrib.python_input import PythonCommandLineInterface, PythonStyle, AutoCompletionStyle
from prompt_toolkit.utils import DummyContext

from six import exec_

import sys
import os
import traceback


__all__ = ('PythonRepl', 'embed')


class PythonRepl(PythonCommandLineInterface):
    def start_repl(self, startup_paths=None):
        """
        Start the Read-Eval-Print Loop.

        :param startup_paths: Array of paths to Python files.
        """
        self._execute_startup(startup_paths)

        # Run REPL loop until Exit.
        try:
            while True:
                # Read
                document = self.read_input(
                    on_abort=AbortAction.RETRY,
                    on_exit=AbortAction.RAISE_EXCEPTION)
                self._process_document(document)
        except Exit:
            pass

    def asyncio_start_repl(self):
        """
        (coroutine) Start a Read-Eval-print Loop for usage in asyncio. E.g.::

            repl = PythonRepl(get_globals=lambda:globals())
            yield from repl.asyncio_start_repl()
        """
        try:
            while True:
                # Read
                g = self.read_input_async(
                    on_abort=AbortAction.RETRY,
                    on_exit=AbortAction.RAISE_EXCEPTION)

                # We use Python 2 syntax for delegating the coroutine and
                # catching the returned document.
                try:
                    while True:
                        yield next(g)
                except StopIteration as e:
                    document = e.args[0]
                    self._process_document(document)
        except Exit:
            pass

    def _process_document(self, document):
        line = document.text

        if line and not line.isspace():
            try:
                # Eval and print.
                self._execute(line)
            except KeyboardInterrupt as e:  # KeyboardInterrupt doesn't inherit from Exception.
                self._handle_keyboard_interrupt(e)
            except Exception as e:
                self._handle_exception(e)

            self.current_statement_index += 1

    def _execute_startup(self, startup_paths):
        """
        Load and execute startup file.
        """
        if startup_paths:
            for path in startup_paths:
                with open(path, 'r') as f:
                    code = compile(f.read(), path, 'exec')
                    exec_(code, self.get_globals(), self.get_locals())

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
                result = eval(line, self.get_globals(), self.get_locals())
                locals = self.get_locals()
                locals['_'] = locals['_%i' % self.current_statement_index] = result

                out_mark = 'Out[%i]: ' % self.current_statement_index

                if result is not None:
                    try:
                        result_str = '%r\n' % result
                    except UnicodeDecodeError:
                        # In Python 2: `__repr__` should return a bytestring,
                        # so to put it in a unicode context could raise an
                        # exception that the 'ascii' codec can't decode certain
                        # characters. Decode as utf-8 in that case.
                        result_str = '%s\n' % repr(result).decode('utf-8')

                # align every line to the first one
                line_sep = '\n' + ' ' * len(out_mark)
                out_string = out_mark + line_sep.join(result_str.splitlines())

                self.stdout.write(out_string)
            # If not a valid `eval` expression, run using `exec` instead.
            except SyntaxError:
                exec_(line, self.get_globals(), self.get_locals())

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
          autocompletion_style=AutoCompletionStyle.POPUP_MENU, startup_paths=None, always_multiline=False,
          patch_stdout=False, return_asyncio_coroutine=False):
    """
    Call this to embed  Python shell at the current point in your program.
    It's similar to `IPython.embed` and `bpython.embed`. ::

        from prompt_toolkit.contrib.repl import embed
        embed(globals(), locals(), vi_mode=False)

    :param vi_mode: Boolean. Use Vi instead of Emacs key bindings.
    """
    globals = globals or {}
    locals = locals or globals

    def get_globals():
        return globals

    def get_locals():
        return locals

    cli = PythonRepl(get_globals, get_locals, vi_mode=vi_mode, history_filename=history_filename,
                     style=(None if no_colors else PythonStyle),
                     autocompletion_style=autocompletion_style, always_multiline=always_multiline)

    patch_context = cli.patch_stdout_context() if patch_stdout else DummyContext()

    if return_asyncio_coroutine:
        def coroutine():
            with patch_context:
                for future in cli.asyncio_start_repl():
                    yield future
        return coroutine()
    else:
        with patch_context:
            cli.start_repl(startup_paths=startup_paths)
