"""
The main `CommandLineInterface` class and logic.
"""
from __future__ import unicode_literals

import os
import signal
import six
import sys
import weakref

from .buffer import Buffer
from .clipboard import Clipboard
from .completion import CompleteEvent
from .focus_stack import FocusStack
from .history import History
from .key_binding.bindings.emacs import load_emacs_bindings
from .key_binding.input_processor import InputProcessor
from .key_binding.registry import Registry
from .layout import Window
from .layout.controls import BufferControl
from .renderer import Renderer
from .utils import EventHook, DummyContext
from .filters import AlwaysOff, AlwaysOn

from pygments.styles.default import DefaultStyle
from types import GeneratorType

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
                 buffer=None,
                 buffers=None,
                 style=None,
                 key_bindings_registry=None,
                 clipboard=None,
                 create_async_autocompleters=True,
                 renderer_factory=Renderer,
                 initial_focussed_buffer='default'):

        assert buffer is None or isinstance(buffer, Buffer)
        assert buffers is None or isinstance(buffers, dict)

        self.stdin = stdin or sys.__stdin__
        self.stdout = stdout or sys.__stdout__
        self.style = style or DefaultStyle
        self.create_async_autocompleters = create_async_autocompleters

        # Events

        #: Called when there is no input for x seconds.
        #: (Fired when any eventloop.onInputTimeout is fired.)
        self.onInputTimeout = EventHook()

        self.onReadInputStart = EventHook()
        self.onReadInputEnd = EventHook()
        self.onReset = EventHook()

        # Focus stack.
        self.focus_stack = FocusStack(initial=initial_focussed_buffer)

        #: The input buffers.
        self.buffers = {
            # We don't make the 'search' and 'system' focussable, that means
            # that window-focus changing functionality is disabled for these.
            # (See prompt_toolkit.key_binding.bindings.utils.focus_next_buffer.)
            # Also, 'returable' is False, in order to block normal Enter/ControlC behaviour.
            'default': (buffer or Buffer(returnable=AlwaysOn())),
            'search': Buffer(history=History(), focussable=AlwaysOff(), returnable=AlwaysOff()),
            'system': Buffer(history=History(), focussable=AlwaysOff(), returnable=AlwaysOff()),
        }
        if buffers:
            self.buffers.update(buffers)

        # When the text in the search buffer changes, set search string in
        # other buffers.
        def search_text_changed():
            search_text = self.buffers['search'].text

            for name, b in self.buffers.items():
                if name != 'search':
                    b.set_search_text(search_text)

        self.buffers['search'].onTextChanged += search_text_changed

        #: The `Layout` instance.
        self.layout = layout or Window(BufferControl())

        #: The clipboard instance
        self.clipboard = clipboard or Clipboard()

        #: The `Renderer` instance.
        self.renderer = renderer_factory(stdout=self.stdout)

        if key_bindings_registry is None:
            key_bindings_registry = Registry()
            load_emacs_bindings(key_bindings_registry)

        #: The `InputProcessor` instance.
        self.input_processor = InputProcessor(key_bindings_registry, weakref.ref(self))

        # Handle events.
        if self.create_async_autocompleters:
            for b in self.buffers.values():
                if b.completer:
                    b.onTextInsert += self._create_async_completer(b)

        self._reset()

        # Event loop.
        self.eventloop = None

    @property
    def is_reading_input(self):
        return bool(self.eventloop)

    @property
    def current_buffer_name(self):
        """
        The name of the current  :class:`Buffer`.
        """
        return self.focus_stack.current

    @property
    def current_buffer(self):
        """
        The current focussed :class:`Buffer`.
        """
        return self.buffers[self.focus_stack.current]

    def add_buffer(self, name, buffer, focus=False):
        """
        Insert a new buffer.
        """
        self.buffers[name] = buffer

        if self.create_async_autocompleters:
            if buffer.completer:
                buffer.onTextInsert += self._create_async_completer(buffer)

        if focus:
            self.focus_stack.replace(name)

    def _reset(self):
        """
        Reset everything, for reading the next input.
        """
        # Notice that we don't reset the buffers. (This happens just before
        # returning, and when we have multiple buffers, we clearly want the
        # content in the other buffers to remain unchanged between several
        # calls of `read_input`. (And the same is true for the `focus_stack`.)

        self._exit_flag = False
        self._abort_flag = False
        self._return_value = None

        self.renderer.reset()
        self.input_processor.reset()
        self.layout.reset()

        # Trigger reset event.
        self.onReset.fire()

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
        self.renderer.render(self, self.layout, self.style)

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

    def read_input(self, on_abort=AbortAction.RETRY, on_exit=AbortAction.IGNORE):
        """
        Read input string from command line.

        :param on_abort: :class:`AbortAction` value. What to do when Ctrl-C has been pressed.
        :param on_exit:  :class:`AbortAction` value. What to do when Ctrl-D has been pressed.
        """
        eventloop = EventLoop(self.input_processor, self.stdin)
        g = self._read_input(on_abort=on_abort,
                             on_exit=on_exit,
                             eventloop=eventloop,
                             return_corountine=False)

        # Return result from `_read_input`.
        try:
            while True:
                next(g)
        except StopIteration as e:
            return e.args[0]

    def read_input_async(self,
                         on_abort=AbortAction.RETRY, on_exit=AbortAction.IGNORE):
        """
        Same as `read_input`, but this returns an asyncio coroutine.

        Warning: this will only work on Python >3.3
        """
        # Inline import, to make sure the rest doesn't break on Python 2
        if sys.platform == 'win32':
            from prompt_toolkit.eventloop.asyncio_win32 import Win32AsyncioEventLoop as AsyncioEventLoop
        else:
            from prompt_toolkit.eventloop.asyncio_posix import PosixAsyncioEventLoop as AsyncioEventLoop

        eventloop = AsyncioEventLoop(self.input_processor, self.stdin)
        return self._read_input(on_abort=on_abort,
                                on_exit=on_exit,
                                eventloop=eventloop,
                                return_corountine=True)

    def _read_input(self, on_abort, on_exit,
                    eventloop, return_corountine):
        """
        The implementation of ``read_input`` which can be called both
        synchronously and asynchronously. When called as coroutine it will
        delegate all the futures from ``eventloop.loop_coroutine``. In both
        cases it returns the result through ``StopIteration``.
        """
        # Set `is_reading_input` flag.
        if self.is_reading_input:
            raise Exception('Already reading input. Read_input is not thread safe.')

        # Create new event loop.
        self.eventloop = eventloop
        self.eventloop.onInputTimeout += lambda: self.onInputTimeout.fire()

        try:
            def reset():
                self._reset()
            reset()

            # Trigger onReadInputStart event.
            self.onReadInputStart.fire()

            with raw_mode(self.stdin.fileno()):
                self.renderer.request_absolute_cursor_position()
                self._redraw()

                with (DummyContext() if sys.platform == 'win32' else
                      call_on_sigwinch(self._on_resize)):
                    while True:
                        if return_corountine:
                            loop_result = self.eventloop.loop_coroutine()
                            assert isinstance(loop_result, GeneratorType)

                            for future in loop_result:
                                yield future
                        else:
                            loop_result = self.eventloop.loop()
                            assert not isinstance(loop_result, GeneratorType)

                        # If the exit flag has been set.
                        if self._exit_flag:
                            self.current_buffer.reset()
                            if on_exit != AbortAction.IGNORE:
                                self._redraw()
                                self.current_buffer.reset()

                            if on_exit == AbortAction.RAISE_EXCEPTION:
                                raise Exit()
                            elif on_exit == AbortAction.RETURN_NONE:
                                raise StopIteration(None)
                            elif on_exit == AbortAction.RETRY:
                                reset()
                                self.renderer.request_absolute_cursor_position()

                        # If the abort flag has been set.
                        if self._abort_flag:
                            if on_abort != AbortAction.IGNORE:
                                self._redraw()
                                self.current_buffer.reset()

                            if on_abort == AbortAction.RAISE_EXCEPTION:
                                raise Abort()
                            elif on_abort == AbortAction.RETURN_NONE:
                                raise StopIteration(None)
                            elif on_abort == AbortAction.RETRY:
                                reset()
                                self.renderer.request_absolute_cursor_position()

                        # If a return value has been set.
                        if self._return_value is not None:
                            self._redraw()
                            self.current_buffer.reset()
                            raise StopIteration(self._return_value)

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

    def set_return_value(self, document):
        self._return_value = document

    def run_in_terminal(self, func):
        """
        Run function on the terminal above the prompt.

        What this does is first hiding the prompt, then running this callable
        (which can safely output to the terminal), and then again rendering the
        prompt which causes the output of this function to scroll above the
        prompt.

        This function is thread safe. It will return immediately and the
        callable will be scheduled in the eventloop of this
        :class:`CommandLineInterface`.
        """
        self.call_from_executor(lambda: self._run_in_terminal(func))

    def _run_in_terminal(self, func):
        """ Blocking, not thread safe version of ``run_in_terminal``. """
        assert self.is_reading_input, 'Should be called while reading input.'
        self.renderer.erase()

        # Run system command.
        with cooked_mode(self.stdin.fileno()):
            func()

        self.renderer.reset()
        self.renderer.request_absolute_cursor_position()
        self._redraw()

    def run_system_command(self, command):
        """
        Run system command (While hiding the prompt. When finished, all the
        output will scroll above the prompt.)

        :param command: Shell command to be executed.
        """
        def run():
            if sys.platform == 'win32':
                os.system(command)  # Needs to be unicode for win32
            else:
                os.system(command.encode('utf-8'))

            (input if six.PY3 else raw_input)('\nPress ENTER to continue...')

        self.run_in_terminal(run)

    def suspend_to_background(self):
        """
        (Not thread safe -- to be called from inside the key bindings.)
        Suspend process.
        """
        def run():
            # Send `SIGSTP` to own process.
            # This will cause it to suspend.
            os.kill(os.getpid(), signal.SIGTSTP)

        self.run_in_terminal(run)

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
        return self._return_value is not None

    @property
    def is_done(self):
        return self.is_exiting or self.is_aborting or self.is_returning

    def _create_async_completer(self, buffer):
        """
        Create function for asynchronous autocompletion while typing.
        (Autocomplete in other thread.)
        """
        complete_thread_running = [False]  # By ref.

        def async_completer():
            document = buffer.document

            # Don't start two threads at the same time.
            if complete_thread_running[0]:
                return

            # Don't complete when we already have completions.
            if buffer.complete_state:
                return

            # Don't automatically complete on empty inputs.
            if not buffer.text:
                return

            # Otherwise, get completions in other thread.
            complete_thread_running[0] = True

            def run():
                completions = list(buffer.completer.get_completions(
                    document,
                    CompleteEvent(text_inserted=True)))
                complete_thread_running[0] = False

                def callback():
                    """
                    Set the new complete_state in a safe way. Don't replace an
                    existing complete_state if we had one. (The user could have
                    pressed 'Tab' in the meantime. Also don't set it if the text
                    was changed in the meantime.
                    """
                    # Set completions if the text was not yet changed.
                    if buffer.text == document.text and \
                            buffer.cursor_position == document.cursor_position and \
                            not buffer.complete_state:
                        buffer._start_complete(go_to_first=False, completions=completions)
                        self._redraw()
                    else:
                        # Otherwise, restart thread.
                        async_completer()
                self.call_from_executor(callback)

            self.run_in_executor(run)
        return async_completer

    def stdout_proxy(self):
        """
        Create an :class:`_StdoutProxy` class which can be used as a patch for
        sys.stdout. Writing to this proxy will make sure that the text appears
        above the prompt, and that it doesn't destroy the output from the
        renderer.
        """
        return _StdoutProxy(self)

    def patch_stdout_context(self):
        """
        Return a context manager that will replace ``sys.stdout`` with a proxy
        that makes sure that all printed text will appear above the prompt, and
        that it doesn't destroy the output from the renderer.
        """
        return _PatchStdoutContext(self.stdout_proxy())


class _PatchStdoutContext(object):
    def __init__(self, new_stdout):
        self.new_stdout = new_stdout

    def __enter__(self):
        self.original_stdout = sys.stdout
        sys.stdout = self.new_stdout

    def __exit__(self, *a, **kw):
        sys.stdout = self.original_stdout


class _StdoutProxy(object):
    """
    Proxy for stdout, as returned by
    :class:`CommandLineInterface.stdout_proxy`.
    """
    def __init__(self, cli):
        self._cli = cli
        self._buffer = []

    def _do(self, func):
        if self._cli.is_reading_input:
            self._cli.run_in_terminal(func)
        else:
            func()

    def write(self, data):
        """
        Note: print()-statements cause to multiple write calls.
              (write('line') and write('\n')). Of course we don't want to call
              `run_in_terminal` for every individual call, because that's too
              expensive, and as long as the newline hasn't been written, the
              text itself is again overwritter by the rendering of the input
              command line. Therefor, we have a little buffer which holds the
              text until a newline is written to stdout.
        """
        if '\n' in data:
            # When there is a newline in the data, write everything before the
            # newline, including the newline itself.
            before, after = data.rsplit('\n', 1)
            to_write = self._buffer + [before, '\n']
            self._buffer = [after]

            def run():
                for s in to_write:
                    self._cli.stdout.write(s)
            self._do(run)
        else:
            # Otherwise, cache in buffer.
            self._buffer.append(data)

    def flush(self):
        """
        Flush buffered output.
        """
        def run():
            for s in self._buffer:
                self._cli.stdout.write(s)
            self._buffer = []
            self._cli.stdout.flush()
        self._do(run)

    def __getattr__(self, name):
        return getattr(self._cli.stdout, name)
