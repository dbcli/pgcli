"""

Adaptor for using the input system of `prompt_toolkit` with the IPython
backend.

This gives a powerful interactive shell that has a nice user interface, but
also the power of for instance all the %-magic functions that IPython has to
offer.

"""
from prompt_toolkit import AbortAction
from prompt_toolkit.code import Completion
from prompt_toolkit.contrib.python_input import PythonCommandLine, PythonPrompt, PythonCommandLine, PythonCode, AutoCompletionStyle
from prompt_toolkit.line import Exit

from IPython.terminal.embed import InteractiveShellEmbed as _InteractiveShellEmbed
from IPython.terminal.ipapp import load_default_config

from pygments.token import Token
from pygments.lexers import PythonLexer, BashLexer, TextLexer


class IPythonPrompt(PythonPrompt):
    @property
    def _prefix(self):
        return (Token.Prompt, 'In [%s]' % self._pythonline._ipython_shell.execution_count)


class IPythonCode(PythonCode):
    def __init__(self, document, globals, locals, magics_manager):
        super(IPythonCode, self).__init__(document, globals, locals)
        self._magics_manager = magics_manager

    @property
    def lexer(self):
        if self.text.lstrip().startswith('!'):
            return BashLexer
        elif self.text.rstrip().endswith('?'):
            return TextLexer
        else:
            return PythonLexer

    def validate(self):
        # Accept magic functions as valid input.
        if self.text.lstrip().startswith('%'):
            return

        # Accept shell input
        if self.text.lstrip().startswith('!'):
            return

        # Accept text ending with '?' or '??'
        # (IPython object inspection.)
        if self.text.rstrip().endswith('?'):
            return

        # Only other, validate as valid Python code.
        super(IPythonCode, self).validate()

    def get_completions(self):
        text = self.document.text_before_cursor.lstrip()

        # Don't complete in shell mode.
        if text.startswith('!'):
            return

        if text.startswith('%'):
            # Complete magic functions.
            text = text[1:]

            for m in self._magics_manager.magics['line']:
                if m.startswith(text):
                    yield Completion(m, m[len(text):])
        else:
            # Complete as normal Python code.
            for c in super(IPythonCode, self).get_completions():
                yield c


class IPythonCommandLine(PythonCommandLine):
    """
    Override our `PythonCommandLine` to add IPython specific stuff.
    """
    def __init__(self, ipython_shell, *a, **kw):
        super(IPythonCommandLine, self).__init__(*a, **kw)
        self._ipython_shell = ipython_shell

    def prompt_factory(self, render_context):
        return IPythonPrompt(render_context, self)

    def code_factory(self, document):
        return IPythonCode(document, self.globals, self.locals, self._ipython_shell.magics_manager)


class InteractiveShellEmbed(_InteractiveShellEmbed):
    """
    Override the `InteractiveShellEmbed` from IPython, to replace the front-end
    with our input shell.
    """
    def __init__(self, *a, **kw):
        vi_mode = kw.pop('vi_mode', False)
        history_filename = kw.pop('history_filename', None)
        autocompletion_style = kw.pop('autocompletion_style', AutoCompletionStyle.POPUP_MENU)

        super(InteractiveShellEmbed, self).__init__(*a, **kw)

        self._cli = IPythonCommandLine(self, vi_mode=vi_mode,
                        history_filename=history_filename, autocompletion_style=autocompletion_style)

    def raw_input(self, prompt=''):
        print('')
        try:
            string = self._cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION).text

            # In case of multiline input, make sure to append a newline to the input,
            # otherwise, IPython will ask again for more input in some cases.
            if '\n' in string:
                return string + '\n\n'
            else:
                return string
        except Exit:
            self.ask_exit()
            return ''


def embed(**kwargs):
    """
    Copied from `IPython/terminal/embed.py`, but using our `InteractiveShellEmbed` instead.
    """
    config = kwargs.get('config')
    header = kwargs.pop('header', u'')
    compile_flags = kwargs.pop('compile_flags', None)
    if config is None:
        config = load_default_config()
        config.InteractiveShellEmbed = config.TerminalInteractiveShell
        kwargs['config'] = config
    shell = InteractiveShellEmbed.instance(**kwargs)
    shell(header=header, stack_depth=2, compile_flags=compile_flags)
