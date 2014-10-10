"""
prompt_toolkit: Pure Python alternative to readline.

Author: Jonathan Slenders
"""
from __future__ import unicode_literals

import errno
import os
import six
import sys

from .key_binding import InputProcessor
from .enums import InputMode
from .key_binding import Registry
from .key_bindings.emacs import emacs_bindings
from .line import Line
from .layout import Layout
from .layout.prompt import DefaultPrompt
from .renderer import Renderer
from .utils import EventHook, DummyContext
from .history import History

from pygments.styles.default import DefaultStyle

import weakref

if sys.platform == 'win32':
    from .terminal.win32_input import raw_mode, cooked_mode
    from .eventloop.win32 import Win32EventLoop as EventLoop
else:
    from .terminal.vt100_input import raw_mode, cooked_mode
    from .eventloop.posix import PosixEventLoop as EventLoop
    from .eventloop.posix import call_on_sigwinch


__all__ = (
    'AbortAction',
    'Exit',
    'Abort',
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

    Typical usage::

        cli = CommandLineInterface()
        while True:
            result = cli.read_input()
            print(result)

    :param stdin: Input stream, by default sys.stdin
    :param stdout: Output stream, by default sys.stdout
    :param layout: :class:`Layout` instance.
    :param style: :class:`Layout` instance.
    :param create_async_autocompleters: Boolean. If True, autocompletions will
        be generated asynchronously while you type.
    """
    def __init__(self, stdin=None, stdout=None,
                 layout=None,
                 line=None,
                 default_input_mode=InputMode.INSERT,
                 style=DefaultStyle,
                 key_binding_factories=None,
                 create_async_autocompleters=True,
                 renderer_factory=Renderer):

        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout

        self.default_input_mode = default_input_mode
        self.style = style

        #: The `Line` instance.
        line = line or Line()
        self.lines = {
            'default': line,
            'search': Line(history=History()),
            'system': Line(history=History()),
        }

        #: The `Layout` instance.
        self.layout = layout or Layout(before_input=DefaultPrompt())

        #: The `Renderer` instance.
        self.renderer = renderer_factory(layout=self.layout,
                                         stdout=self.stdout,
                                         style=self.style)

        key_binding_factories = key_binding_factories or [emacs_bindings]

        #: The `InputProcessor` instance.
        self.input_processor = self._create_input_processor(key_binding_factories)

        # Handle events.
        if create_async_autocompleters:
            for n, l in self.lines.items():
                if l.completer:
                    l.onTextInsert += self._create_async_completer(n)

        self._reset()

        # Event loop.
        self.eventloop = None

        # Events

        #: Called when there is no input for x seconds.
        #: (Fired when any eventloop.onInputTimeout is fired.)
        self.onInputTimeout = EventHook()

        self.onReadInputStart = EventHook()
        self.onReadInputEnd = EventHook()

    @property
    def is_reading_input(self):
        return bool(self.eventloop)

    @property
    def line(self):
        return self.lines['default']

    def _create_input_processor(self, key_binding_factories):
        """
        Create :class:`InputProcessor` instance.
        """
        key_registry = Registry()
        for kb in key_binding_factories:
            kb(key_registry, weakref.ref(self))

        #: The `InputProcessor` instance.
        return InputProcessor(key_registry)

    def _reset(self, initial_value=''):
        """
        Reset everything.
        """
        self._exit_flag = False
        self._abort_flag = False
        self._return_code = None

        for l in self.lines.values():
            l.reset()

        self.line.reset(initial_value=initial_value)
        self.renderer.reset()
        self.input_processor.reset(default_input_mode=self.default_input_mode)
        self.layout.reset()

    def request_redraw(self):
        """
        Thread safe way of sending a repaint trigger to the input event loop.
        """
        if self.is_reading_input:
            self.call_from_executor(self._redraw)

    def _redraw(self):
        """
        Render the command line again. (Not thread safe!)
        (From other threads, or if unsure, use `request_redraw`.)
        """
        self.renderer.render(self)

    def run_in_executor(self, callback):
        """
        Run a long running function in a background thread.
        (This is recommended for code that could block the `read_input` event
        loop.)
        Similar to Twisted's ``deferToThread``.

        :param callback: The callable that should run in the executor.
        """
        self.eventloop.run_in_executor(callback)

    def call_from_executor(self, callback):
        """
        Call this function in the main event loop.
        Similar to Twisted's ``callFromThread``.

        :param callback: The callable that should run in the main event loop.
        """
        if self.eventloop:
            self.eventloop.call_from_executor(callback)
            return True
        else:
            return False

    def _on_resize(self):
        """
        When the window size changes, we erase the current output and request
        again the cursor position. We the CPR answer arrives, the output is
        drawn again.
        (We do it asynchronously, because writing to the output from inside the
        signal handler causes easily reentrant calls, giving runtime errors.)
        """
        assert self.eventloop

        def do_in_event_loop():
            self.renderer.erase()
            self.renderer.request_absolute_cursor_position()
        self.call_from_executor(do_in_event_loop)

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

        # Create new event loop.
        self.eventloop = EventLoop(self.input_processor, self.stdin)
        self.eventloop.onInputTimeout += lambda: self.onInputTimeout.fire()

        try:
            def reset():
                self._reset(initial_value=initial_value)
            reset()

            # Trigger onReadInputStart event.
            self.onReadInputStart.fire()

            with raw_mode(self.stdin.fileno()):
                self.renderer.request_absolute_cursor_position()

                self._redraw()

                with (DummyContext() if sys.platform == 'win32' else
                      call_on_sigwinch(self._on_resize)):
                    while True:
                        self.eventloop.loop()

                        # If the exit flag has been set.
                        if self._exit_flag:
                            if on_exit != AbortAction.IGNORE:
                                self.renderer.render(self)

                            if on_exit == AbortAction.RAISE_EXCEPTION:
                                raise Exit()
                            elif on_exit == AbortAction.RETURN_NONE:
                                return None
                            elif on_exit == AbortAction.RETRY:
                                reset()
                                self.renderer.request_absolute_cursor_position()

                        # If the abort flag has been set.
                        if self._abort_flag:
                            if on_abort != AbortAction.IGNORE:
                                self.renderer.render(self)

                            if on_abort == AbortAction.RAISE_EXCEPTION:
                                raise Abort()
                            elif on_abort == AbortAction.RETURN_NONE:
                                return None
                            elif on_abort == AbortAction.RETRY:
                                reset()
                                self.renderer.request_absolute_cursor_position()

                        # If a return value has been set.
                        if self._return_code:
                            self.renderer.render(self)
                            return self._return_code

                        # Now render the current layout to the output.
                        self._redraw()

        finally:
            # Close event loop
            self.eventloop.close()
            self.eventloop = None

            # Trigger onReadInputEnd event.
            self.onReadInputEnd.fire()

    def set_exit(self):
        self._exit_flag = True

    def set_abort(self):
        self._abort_flag = True

    def set_return_value(self, code):
        self._return_code = code

    def run_system_command(self, command):
        """
        (Not thread safe -- to be called from inside the key bindings.)
        Run system command.

        :param command: Shell command to be executed.
        """
        assert self.is_reading_input, 'Should be called while reading input.'

        self.renderer.erase()

        # Run system command.
        with cooked_mode(self.stdin.fileno()):
            if sys.platform == 'win32':
                os.system(command)  # Needs to be unicode for win32
            else:
                os.system(command.encode('utf-8'))

            (input if six.PY3 else raw_input)('\nPress ENTER to continue...')

        self.renderer.reset()
        self.renderer.request_absolute_cursor_position()

    def suspend_to_background(self):
        """
        (Not thread safe -- to be called from inside the key bindings.)
        Suspend process.
        """
        assert self.is_reading_input, 'Should be called while reading input.'

        self.renderer.erase()

        # Make sure to be in cooked mode when suspending.
        with cooked_mode(self.stdin.fileno()):
            # Send `SIGSTP` to own process.
            # This will cause it to suspend.
            os.kill(os.getpid(), signal.SIGTSTP)

        self.renderer.reset()
        self.renderer.request_absolute_cursor_position()

    @property
    def is_exiting(self):
        """
        ``True`` when the exit flag as been set.
        """
        return self._exit_flag

    @property
    def is_aborting(self):
        """
        ``True`` when the abort flag as been set.
        """
        return self._abort_flag

    @property
    def is_returning(self):
        """
        ``True`` when a return value has been set.
        """
        return self._return_code

    def _create_async_completer(self, line_name):
        """
        Create function for asynchronous autocompletion while typing.
        (Autocomplete in other thread.)
        """
        line = self.lines[line_name]
        complete_thread_running = [False]  # By ref.

        def async_completer():
            document = line.document

            # Don't start two threads at the same time.
            if complete_thread_running[0]:
                return

            # Don't complete when we already have completions.
            if line.complete_state:
                return

            # Don't automatically complete on empty inputs.
            char = document.char_before_cursor
            if not line.text or char.isspace():
                return

            # Otherwise, get completions in other thread.
            complete_thread_running[0] = True

            def run():
                completions = list(line.completer.get_completions(document))
                complete_thread_running[0] = False

                def callback():
                    """
                    Set the new complete_state in a safe way. Don't replace an
                    existing complete_state if we had one. (The user could have
                    pressed 'Tab' in the meantime. Also don't set it if the text
                    was changed in the meantime.
                    """
                    # Set completions if the text was not yet changed.
                    if line.text == document.text and \
                            line.cursor_position == document.cursor_position and \
                            not line.complete_state:
                        line._start_complete(go_to_first=False, completions=completions)
                        self._redraw()
                    else:
                        # Otherwise, restart thread.
                        async_completer()
                self.call_from_executor(callback)

            self.run_in_executor(run)
        return async_completer
