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

import codecs
import fcntl
import os
import select
import six
import sys
import errno
import threading

from .code import Code
from .inputstream import InputStream
from .inputstream_handler import InputStreamHandler
from .line import Line, Exit, ReturnInput, Abort
from .prompt import Prompt
from .renderer import Renderer
from .utils import raw_mode, call_on_sigwinch
from .history import History

from pygments.styles.default import DefaultStyle

__all__ = (
        'AbortAction',
        'CommandLine',
)

class AbortAction:
    """
    Actions to take on an Exit or Abort exception.
    """
    IGNORE = 'ignore'
    RETRY = 'retry'
    RAISE_EXCEPTION = 'raise-exception'
    RETURN_NONE = 'return-none'


class CommandLine(object):
    """
    Wrapper around all the other classes, tying everything together.
    """
            # TODO: rename `_cls` suffixes to `_factory`

    #: The `Line` class which implements the text manipulation.
    line_cls = Line

    #: A `Code` class which implements the interpretation of the text input.
    #: It tokenizes/parses the input text.
    code_cls = Code

    #: `Prompt` class for the layout of the prompt. (and the help text.)
    prompt_cls = Prompt

    #: `InputStream` class for the parser of the input
    #: (Normally, you don't override this one.)
    inputstream_cls = InputStream

    #: `InputStreamHandler` class for the keybindings.
    inputstream_handler_cls = InputStreamHandler

    #: `Renderer` class.
    renderer_cls = Renderer

    #: `pygments.style.Style` class for the syntax highlighting.
    style_cls = DefaultStyle

    #: `History` class.
    history_cls = History

    #: Boolean to indicate whether we will have other threads communicating
    #: with the input event loop.
    enable_concurency = False

    #: When to call the `on_input_timeout` callback.
    input_timeout = .5

    def __init__(self, stdin=None, stdout=None):
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout

        # In case of Python2, sys.stdin.read() returns bytes instead of unicode
        # characters. By wrapping it in getreader('utf-8'), we make sure to
        # read valid unicode characters.
        if not six.PY3:
            self.stdin = codecs.getreader('utf-8')(sys.stdin)

        self._renderer = self.renderer_cls(self.stdout, style=self.style_cls)
        self._line = self.line_cls(renderer=self._renderer,
                        code_cls=self.code_cls, prompt_cls=self.prompt_cls,
                        history_cls=self.history_cls)
        self._inputstream_handler = self.inputstream_handler_cls(self._line)

        # Pipe for inter thread communication.
        self._redraw_pipe = None

        #: Currently reading input.
        self.is_reading_input = False

    def request_redraw(self):
        """
        Thread safe way of sending a repaint trigger to the input event loop.
        """
        assert self.enable_concurency

        if self._redraw_pipe:
            os.write(self._redraw_pipe[1], b'x')

    def _redraw(self):
        """
        Render the command line again. (Not thread safe!)
        (From other threads, or if unsure, use `request_redraw`.)
        """
        assert self.enable_concurency

        self._renderer.render(self._line.get_render_context())

    def run_in_executor(self, callback):
        """
        Run a long running function in a background thread.
        (This is recommended for code that could block the `read_input` event
        loop.)
        """
        assert self.enable_concurency

        class _Thread(threading.Thread):
            def run(t):
                callback()

        _Thread().start()

    def on_input_timeout(self, code_obj):
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
                # Read the input and return it.
                # Note: the following works better than wrapping `self.stdin` like
                #       `codecs.getreader('utf-8')(stdin)` and doing `read(1)`.
                #       Somehow that causes some latency when the escape
                #       character is pressed.
                return os.read(self.stdin.fileno(), 1024).decode('utf-8')

            # If we receive something on our redraw pipe, render again.
            elif self._redraw_pipe[0] in r:
                # Flush all the pipe content and repaint.
                os.read(self._redraw_pipe[0], 1024)
                self._redraw()
                timeout = None
            else:
                #
                self.on_input_timeout(self._line.create_code_obj())
                timeout = None


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
            if self.enable_concurency:
                self._redraw_pipe = os.pipe()

                # Make the read-end of this pipe non blocking.
                fcntl.fcntl(self._redraw_pipe[0], fcntl.F_SETFL, os.O_NONBLOCK)

            # TODO: create renderer here. (We want a new rendere instance for each input.)
            #       `_line` should not need the renderer instance...
            #       (use exceptions there to print completion pagers.)

            stream = self.inputstream_cls(self._inputstream_handler, stdout=self.stdout)

            def reset_line():
                # Reset line
                self._line.reset(initial_value=initial_value)
            reset_line()

            # Trigger read_start.
            self.on_read_input_start()

            with raw_mode(self.stdin):
                self._redraw()

                with call_on_sigwinch(self._redraw):
                    while True:
                        if self.enable_concurency:
                            c = self._get_char_loop()
                        else:
                            c = self.stdin.read(1)

                        # If we got a character, feed it to the input stream. If we
                        # got none, it means we got a repaint request.
                        if c:
                            try:
                                # Feed one character at a time. Feeding can cause the
                                # `Line` object to raise Exit/Abort/ReturnInput
                                stream.feed(c)

                            except Exit as e:
                                # Handle exit.
                                if on_exit != AbortAction.IGNORE:
                                    self._renderer.render(e.render_context)

                                if on_exit == AbortAction.RAISE_EXCEPTION:
                                    raise
                                elif on_exit == AbortAction.RETURN_NONE:
                                    return None
                                elif on_exit == AbortAction.RETRY:
                                    reset_line()

                            except Abort as abort:
                                # Handle abort.
                                if on_abort != AbortAction.IGNORE:
                                    self._renderer.render(abort.render_context)

                                if on_abort == AbortAction.RAISE_EXCEPTION:
                                    raise
                                elif on_abort == AbortAction.RETURN_NONE:
                                    return None
                                elif on_abort == AbortAction.RETRY:
                                    reset_line()

                            except ReturnInput as input:
                                self._renderer.render(input.render_context)
                                return input.document

                        # TODO: completions should be 'rendered' as well through an exception.

                        # Now render the current prompt to the output.
                        # TODO: unless `select` tells us that there's another character to feed.
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


def _select(*args, **kwargs):
    """
    Wrapper around select.select.

    When the SIGWINCH signal is handled, other system calls, like select
    are aborted in Python. This wrapper will retry the system call.
    """
    while True:
        try:
            return select.select(*args, **kwargs)
        except Exception as e:
            # Retry select call when EINTR
            if e.args and e.args[0] == errno.EINTR:
                continue
            else:
                raise
