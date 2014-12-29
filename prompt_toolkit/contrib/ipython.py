"""

Adaptor for using the input system of `prompt_toolkit` with the IPython
backend.

This gives a powerful interactive shell that has a nice user interface, but
also the power of for instance all the %-magic functions that IPython has to
offer.

"""
from __future__ import unicode_literals
from prompt_toolkit import AbortAction
from prompt_toolkit.completion import Completion
from prompt_toolkit.contrib.python_input import PythonCommandLineInterface, PythonValidator, PythonCompleter
from prompt_toolkit import Exit
from prompt_toolkit.document import Document
from prompt_toolkit.layout.controls import TokenListControl

from IPython.terminal.embed import InteractiveShellEmbed as _InteractiveShellEmbed
from IPython.terminal.ipapp import load_default_config
from IPython import utils as ipy_utils
from IPython.core.inputsplitter import IPythonInputSplitter

from pygments.lexers import PythonLexer, BashLexer, TextLexer
from pygments.token import Token


class IPythonPrompt(TokenListControl):
    """
    Prompt showing something like "In [1]:".
    """
    def __init__(self, prompt_manager):
        def get_tokens(cli):
            text = prompt_manager.render('in', color=False, just=False)
            return [(Token.Layout.Prompt, text)]

        super(IPythonPrompt, self).__init__(get_tokens)


class IPythonValidator(PythonValidator):
    def __init__(self, *args, **kwargs):
        super(IPythonValidator, self).__init__(*args, **kwargs)
        self.isp = IPythonInputSplitter()

    def validate(self, document):
        document = Document(text=self.isp.transform_cell(document.text))
        super(IPythonValidator, self).validate(document)


class IPythonCompleter(PythonCompleter):
    def __init__(self, get_globals, get_locals, magics_manager):
        super(IPythonCompleter, self).__init__(get_globals, get_locals)
        self._magics_manager = magics_manager

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lstrip()

        # Don't complete in shell mode.
        if text.startswith('!'):
            return

        if text.startswith('%'):
            # Complete magic functions.
            for m in self._magics_manager.magics['line']:
                if m.startswith(text[1:]):
                    yield Completion('%%%s' % m, -len(text))
        else:
            # Complete as normal Python code.
            for c in super(IPythonCompleter, self).get_completions(document, complete_event):
                yield c


# TODO: Use alternate lexers in layout, if we have a ! prefix or ? suffix.
#    @property
#    def lexer(self):
#        if self.text.lstrip().startswith('!'):
#            return BashLexer
#        elif self.text.rstrip().endswith('?'):
#            return TextLexer
#        else:
#            return PythonLexer


class IPythonCommandLineInterface(PythonCommandLineInterface):
    """
    Override our `PythonCommandLineInterface` to add IPython specific stuff.
    """
    def __init__(self, ipython_shell, *a, **kw):
        kw['_completer'] = IPythonCompleter(kw['get_globals'], kw['get_globals'], ipython_shell.magics_manager)
        kw['_validator'] = IPythonValidator()
        kw['_python_prompt_control'] = IPythonPrompt(ipython_shell.prompt_manager)

        super(IPythonCommandLineInterface, self).__init__(*a, **kw)
        self.ipython_shell = ipython_shell


class InteractiveShellEmbed(_InteractiveShellEmbed):
    """
    Override the `InteractiveShellEmbed` from IPython, to replace the front-end
    with our input shell.
    """
    def __init__(self, *a, **kw):
        vi_mode = kw.pop('vi_mode', False)
        history_filename = kw.pop('history_filename', None)

        super(InteractiveShellEmbed, self).__init__(*a, **kw)

        def get_globals():
            return self.user_ns

        self._cli = IPythonCommandLineInterface(
            self, get_globals=get_globals, vi_mode=vi_mode,
            history_filename=history_filename)

    def raw_input(self, prompt=''):
        print('')
        try:
            string = self._cli.cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION).text

            # In case of multiline input, make sure to append a newline to the input,
            # otherwise, IPython will ask again for more input in some cases.
            if '\n' in string:
                return string + '\n\n'
            else:
                return string
        except Exit:
            self.ask_exit()
            return ''


def initialize_extensions(shell, extensions):
    """
    Partial copy of `InteractiveShellApp.init_extensions` from IPython.
    """
    try:
        iter(extensions)
    except TypeError:
        pass  # no extensions found
    else:
        for ext in extensions:
            try:
                shell.extension_manager.load_extension(ext)
            except:
                ipy_utils.warn.warn(
                    "Error in loading extension: %s" % ext +
                    "\nCheck your config files in %s" % ipy_utils.path.get_ipython_dir())
                shell.showtraceback()


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
    initialize_extensions(shell, config['InteractiveShellApp']['extensions'])
    shell(header=header, stack_depth=2, compile_flags=compile_flags)
