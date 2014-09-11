"""

prompt_toolkit
--------------

Pure Python alternative to readline.

Still experimental and incomplete. It should be able to handle RAW vt100 input
sequences for a command line and construct a command line with autocompletion
there.

Author: Jonathan Slenders

"""
from __future__ import unicode_literals

import fcntl
import os
import select
import sys
import errno
import threading

from codecs import getincrementaldecoder

from .code import Code
from .inputstream import InputStream
from .key_binding import InputProcessor
from .enums import InputMode
from .key_binding import Registry
from .key_bindings.emacs import emacs_bindings
from .line import Line, Callbacks
from .prompt import Prompt
from .renderer import Renderer
from .utils import raw_mode, call_on_sigwinch
from .history import History

from pygments.styles.default import DefaultStyle

import weakref


__all__ = (
        'AbortAction',
        'CommandLineInterface',
)

class AbortAction:
    """
    Actions to take on an Exit or Abort exception.
    """
    IGNORE = 'ignore'
    RETRY = 'retry'
    RAISE_EXCEPTION = 'raise-exception'
    RETURN_NONE = 'return-none'


class Exit(Exception):
    pass


class Abort(Exception):
    pass


class CommandLineInterface(object):
    """
    Wrapper around all the other classes, tying everything together.
    """
    # All the factories below have to be callables that return instances of the
    # respective classes. They can be as simple as the class itself, but they
    # can also be instance methods that pass some additional parameters to the
    # class.

    #: The `Line` class which implements the text manipulation.
    line_factory = Line

    #: A `Code` class which implements the interpretation of the input string.
    #: It tokenizes/parses the input text.
    code_factory = Code

    #: `Prompt` class for the layout of the prompt. (and the help text.)
    prompt_factory = Prompt

    #: `InputStream` class for the parser of the input
    #: (Normally, you don't override this one.)
    inputstream_factory = InputStream

    #: `InputStreamHandler` class for the keybindings.
    key_bindings_factories = [ emacs_bindings ]
    default_input_mode = InputMode.INSERT

    #: `Renderer` class.
    renderer_factory = Renderer

    #: `History` class.
    history_factory = History

    #: `pygments.style.Style` class for the syntax highlighting.
    style = DefaultStyle

    #: When to call the `on_input_timeout` callback.
    input_timeout = .5

    stdin_decoder_cls = getincrementaldecoder('utf-8')

    def __init__(self, stdin=None, stdout=None):
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout

        #: The `Line` instance.
                    # TODO: construct the `Line` object outside of this constructor.
                    #       A commandline should be able to have several `Line` instances.
                    #       e.g. one for the incremental-search input, one for
                    #       another document, etc...
        self.line = self.line_factory(
                                code_factory=self.code_factory,
                                history_factory=self.history_factory,
                                callbacks=LineCallbacks(self))

        key_registry = Registry()
        for kb in self.key_bindings_factories:
            kb(key_registry, weakref.ref(self))

        #: The `InputProcessor` instance.
        self.input_processor = InputProcessor(key_registry, default_input_mode=self.default_input_mode)

        #: The `prompt` instance.
        self.prompt = self.prompt_factory(weakref.ref(self))

        #: The `Renderer` instance.
        self.renderer = self.renderer_factory(
                                prompt=self.prompt,
                                stdout=self.stdout,
                                style=self.style)

        # Pipe for inter thread communication.
        self._redraw_pipe = None

        #: Currently reading input.
        self.is_reading_input = False

        # Create incremental decoder for decoding stdin.
        # We can not just do `os.read(stdin.fileno(), 1024).decode('utf-8')`, because
        # it could be that we are in the middle of a utf-8 byte sequence.
        self._stdin_decoder = self.stdin_decoder_cls()

        self._reset()

    def _reset(self):
        self._exit_flag = False
        self._abort_flag = False
        self._return_code = None

    def request_redraw(self):
        """
        Thread safe way of sending a repaint trigger to the input event loop.
        """
        if self._redraw_pipe:
            os.write(self._redraw_pipe[1], b'x')

    def _redraw(self):
        """
        Render the command line again. (Not thread safe!)
        (From other threads, or if unsure, use `request_redraw`.)
        """
        self.renderer.render()

    def run_in_executor(self, callback):
        """
        Run a long running function in a background thread.
        (This is recommended for code that could block the `read_input` event
        loop.)
        """
        class _Thread(threading.Thread):
            def run(t):
                callback()

        _Thread().start()

    def on_input_timeout(self):
        """
        Called when there is no input for x seconds.
        """
        # At this place, you can for instance start a background thread to
        # generate information about the input. E.g. the code signature of the
        # function below the cursor position in the case of a REPL.
        pass

    def on_read_input_start(self):
        pass

    def on_read_input_end(self):
        pass

    def _get_char_loop(self):
        """
        The input 'event loop'.

        This should return the next character to process.
        """
        timeout = self.input_timeout

        while True:
            r, w, x = _select([self.stdin, self._redraw_pipe[0]], [], [], timeout)

            if self.stdin in r:
                return self._read_from_stdin()

            # If we receive something on our redraw pipe, render again.
            elif self._redraw_pipe[0] in r:
                # Flush all the pipe content and repaint.
                os.read(self._redraw_pipe[0], 1024)
                self._redraw()
                timeout = None
            else:
                #
                self.on_input_timeout()
                timeout = None

    def _read_from_stdin(self):
        """
        Read the input and return it.
        """
        # Note: the following works better than wrapping `self.stdin` like
        #       `codecs.getreader('utf-8')(stdin)` and doing `read(1)`.
        #       Somehow that causes some latency when the escape
        #       character is pressed. (Especially on combination with the `select`.
        try:
            bytes = os.read(self.stdin.fileno(), 1024)
        except OSError:
            # In case of SIGWINCH
            bytes = b''

        try:
            return self._stdin_decoder.decode(bytes)
        except UnicodeDecodeError:
            # When it's not possible to decode this bytes, reset the decoder.
            # The only occurence of this that I had was when using iTerm2 on OS
            # X, with "Option as Meta" checked (You should choose "Option as
            # +Esc".)
            self._stdin_decoder = self.stdin_decoder_cls()
            return ''

    def read_input(self, initial_value='', on_abort=AbortAction.RETRY, on_exit=AbortAction.IGNORE):
        """
        Read input string from command line.

        :param initial_value: The original value of the input string.
        :param on_abort: :class:`AbortAction` value. What to do when Ctrl-C has been pressed.
        :param on_exit:  :class:`AbortAction` value. What to do when Ctrl-D has been pressed.
        """
        # Set `is_reading_input` flag.
        if self.is_reading_input:
            raise Exception('Already reading input. Read_input is not thread safe.')

        self.is_reading_input = True

        try:
            # Create a pipe for inter thread communication.
            self._redraw_pipe = os.pipe()
            fcntl.fcntl(self._redraw_pipe[0], fcntl.F_SETFL, os.O_NONBLOCK)

            stream = self.inputstream_factory(self.input_processor, stdout=self.stdout)

            def reset_line():
                """ Reset everything. """
                stream.reset()
                self.line.reset(initial_value=initial_value)
                self.renderer.reset()
                self.input_processor.reset()
                self._reset()
            reset_line()

            # Trigger read_start.
            self.on_read_input_start()

            with raw_mode(self.stdin.fileno()):
                self._redraw()

                # When the window size changes, we do a redraw request call.
                # (We do it asynchronously, because doing the actual drawing
                # inside the signal handler causes easily reentrant calls,
                # giving runtime errors.)
                with call_on_sigwinch(self.request_redraw):
                    while True:
                        c = self._get_char_loop()

                        # If we got a character, feed it to the input stream. If we
                        # got none, it means we got a repaint request.
                        if c:
                            # Feed input text.
                            stream.feed(c)

                        # If the exit flag has been set.
                        if self._exit_flag:
                            if on_exit != AbortAction.IGNORE:
                                self.renderer.render(abort=True)

                            if on_exit == AbortAction.RAISE_EXCEPTION:
                                raise Exit()
                            elif on_exit == AbortAction.RETURN_NONE:
                                return None
                            elif on_exit == AbortAction.RETRY:
                                reset_line()

                        # If the abort flag has been set.
                        if self._abort_flag:
                            if on_abort != AbortAction.IGNORE:
                                self.renderer.render(abort=True)

                            if on_abort == AbortAction.RAISE_EXCEPTION:
                                raise Abort()
                            elif on_abort == AbortAction.RETURN_NONE:
                                return None
                            elif on_abort == AbortAction.RETRY:
                                reset_line()

                        # If a return value has been set.
                        if self._return_code:
                            self.renderer.render(accept=True)
                            return self._return_code

                        # Now render the current prompt to the output.
                        self._redraw()

        finally:
            # Close redraw pipes.
            redraw_pipe = self._redraw_pipe
            self._redraw_pipe = None

            if redraw_pipe:
                os.close(redraw_pipe[0])
                os.close(redraw_pipe[1])

            # Trigger read_end.
            self.on_read_input_end()

            self.is_reading_input = False

    def set_exit(self):
        self._exit_flag = True

    def set_abort(self):
        self._abort_flag = True

    def set_return_value(self, code):
        self._return_code = code


class LineCallbacks(Callbacks):
    """
    Callback handlers for the `Line`
    """
    def __init__(self, command_line):
        self.command_line = command_line

    def clear_screen(self):
        self.command_line.renderer.clear()

    def exit(self):
        self.command_line.set_exit()

    def abort(self):
        self.command_line.set_abort()

    def return_input(self, code):
        self.command_line.set_return_value(code)


def _select(*args, **kwargs):
    """
    Wrapper around select.select.

    When the SIGWINCH signal is handled, other system calls, like select
    are aborted in Python. This wrapper will retry the system call.
    """
    while True:
        try:
            return select.select(*args, **kwargs)
        except select.error as e:
            # Retry select call when EINTR
            if e.args and e.args[0] == errno.EINTR:
                continue
            else:
                raise
