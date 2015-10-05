"""
The main `CommandLineInterface` class and logic.
"""
from __future__ import unicode_literals

import functools
import os
import signal
import six
import sys
import threading
import weakref

from .application import Application, AbortAction
from .buffer import Buffer, AcceptAction
from .completion import CompleteEvent
from .completion import get_common_complete_suffix
from .enums import DEFAULT_BUFFER, SEARCH_BUFFER, SYSTEM_BUFFER, DUMMY_BUFFER
from .eventloop.base import EventLoop
from .eventloop.callbacks import EventLoopCallbacks
from .filters import Condition
from .history import InMemoryHistory
from .input import StdinInput, Input
from .key_binding.input_processor import InputProcessor
from .output import Output
from .renderer import Renderer, print_tokens
from .search_state import SearchState
from .utils import is_windows

from types import GeneratorType


__all__ = (
    'AbortAction',
    'CommandLineInterface',
)


class CommandLineInterface(object):
    """
    Wrapper around all the other classes, tying everything together.

    Typical usage::

        cli = CommandLineInterface(eventloop)
        while True:
            result = cli.run()
            print(result)

    :param eventloop: The `EventLoop` to be used when `run` is called.
                      (Further, this allows callbacks to know where to find the
                      `run_in_executor`.) It can be `None` as well, when no
                      eventloop is used/exposed.
    :param application: `Application` .
    :param input: :class:`Input` class.
    :param output: :class:`Output` instance. (Probably Vt100_Output or Win32Output.)
    """
    def __init__(self, application, eventloop=None, input=None, output=None):
        assert isinstance(application, Application)
        assert eventloop is None or isinstance(eventloop, EventLoop)
        assert output is None or isinstance(output, Output)
        assert input is None or isinstance(input, Input)

        from .shortcuts import create_default_output, create_eventloop

        self.application = application
        self.eventloop = eventloop or create_eventloop()
        self._is_running = False

        # Inputs and outputs.
        self.output = output or create_default_output()
        self.input = input or StdinInput(sys.stdin)

        #: The input buffers.
        self.buffers = {
            # For the 'search' and 'system' buffers, 'returnable' is False, in
            # order to block normal Enter/ControlC behaviour.
            DEFAULT_BUFFER: (application.buffer or Buffer(accept_action=AcceptAction.RETURN_DOCUMENT)),
            SEARCH_BUFFER: Buffer(history=InMemoryHistory(), accept_action=AcceptAction.IGNORE),
            SYSTEM_BUFFER: Buffer(history=InMemoryHistory(), accept_action=AcceptAction.IGNORE),
            DUMMY_BUFFER: Buffer(read_only=True),
        }
        self.buffers.update(application.buffers)

        #: The `Renderer` instance.
        # Make sure that the same stdout is used, when a custom renderer has been passed.
        self.renderer = Renderer(
            self.output,
            use_alternate_screen=application.use_alternate_screen,
            mouse_support=application.mouse_support)

        # Invalidate flag. When 'True', a repaint has been scheduled.
        self._invalidated = False

        #: The `InputProcessor` instance.
        self.input_processor = InputProcessor(application.key_bindings_registry, weakref.ref(self))

        self._async_completers = {}  # Map buffer name to completer function.

        # Pointer to sub CLI. (In chain of CLI instances.)
        self._sub_cli = None  # None or other CommandLineInterface instance.

        # Call `add_buffer` for each buffer.
        for name, b in self.buffers.items():
            self.add_buffer(name, b)

        self.reset()

        # Trigger initialize callback.
        self.application.on_initialize.fire(self)

    @property
    def layout(self):
        return self.application.layout

    @property
    def clipboard(self):
        return self.application.clipboard

    @property
    def focus_stack(self):
        return self.application.focus_stack

    def add_buffer(self, name, buffer, focus=False):
        """
        Insert a new buffer.
        """
        assert isinstance(buffer, Buffer)
        self.buffers[name] = buffer

        if focus:
            self.focus_stack.replace(name)

        # Create asynchronous completer / auto suggestion.
        auto_suggest_function = self._create_auto_suggest_function(buffer)
        completer_function = self._create_async_completer(buffer)
        self._async_completers[name] = completer_function

        # Complete/suggest on text insert.
        def create_on_insert_handler():
            """
            Wrapper around the asynchronous completer and auto suggestion, that
            ensures that it's only called while typing if the
            `complete_while_typing` filter is enabled.
            """
            def on_text_insert():
                # Only complete when "complete_while_typing" is enabled.
                if buffer.completer and buffer.complete_while_typing():
                    completer_function()

                # Call auto_suggest.
                if buffer.auto_suggest:
                    auto_suggest_function()

                # Trigger on_buffer_changed when text in this buffer changes.
                self.application.on_buffer_changed.fire(self)

            return on_text_insert

        buffer.on_text_insert += create_on_insert_handler()

    def start_completion(self, buffer_name=None, select_first=False,
                         select_last=False, insert_common_part=False,
                         complete_event=None):
        """
        Start asynchronous autocompletion of this buffer.
        (This will do nothing if a previous completion was still in progress.)
        """
        buffer_name = buffer_name or self.current_buffer_name
        completer = self._async_completers.get(buffer_name)

        if completer:
            completer(select_first=select_first,
                      select_last=select_last,
                      insert_common_part=insert_common_part,
                      complete_event=CompleteEvent(completion_requested=True))

    @property
    def current_buffer_name(self):
        """
        The name of the current  :class:`Buffer`. (Or `None`.)
        """
        return self.focus_stack.current

    @property
    def current_buffer(self):
        """
        The current focussed :class:`Buffer`.

        (This returns a dummy `Buffer` when none of the actual buffers has the
        focus. In this case, it's really not practical to check for `None`
        values or catch exceptions every time.)
        """
        name = self.focus_stack.current
        if name is not None:
            return self.buffers[self.focus_stack.current]
        else:
            return self.buffers[DUMMY_BUFFER]

    @property
    def terminal_title(self):
        """
        Return the current title to be displayed in the terminal.
        When this in `None`, the terminal title remains the original.
        """
        result = self.application.get_title()

        # Make sure that this function returns a unicode object,
        # and not a byte string.
        assert result is None or isinstance(result, six.text_type)
        return result

    @property
    def is_searching(self):
        """
        True when we are searching.
        """
        return self.current_buffer_name == SEARCH_BUFFER

    def reset(self, reset_current_buffer=False):
        """
        Reset everything, for reading the next input.

        :param reset_current_buffer: If True, also reset the focussed buffer.
        """
        # Notice that we don't reset the buffers. (This happens just before
        # returning, and when we have multiple buffers, we clearly want the
        # content in the other buffers to remain unchanged between several
        # calls of `run`. (And the same is true for the `focus_stack`.)

        self._exit_flag = False
        self._abort_flag = False

        self._return_value = None

        self.renderer.reset()
        self.input_processor.reset()
        self.layout.reset()

        if reset_current_buffer:
            self.current_buffer.reset()

        # Search new search state. (Does also remember what has to be
        # highlighted.)
        self.search_state = SearchState(ignore_case=Condition(lambda: self.is_ignoring_case))

        # Trigger reset event.
        self.application.on_reset.fire(self)

    @property
    def in_paste_mode(self):
        """ True when we are in paste mode. """
        return self.application.paste_mode(self)

    @property
    def is_ignoring_case(self):
        """ True when we currently ignore casing. """
        return self.application.ignore_case(self)

    def request_redraw(self):
        """
        Thread safe way of sending a repaint trigger to the input event loop.
        """
        if self.eventloop is not None:
            # Never schedule a second redraw, when a previous one has not yet been
            # executed. (This should protect against other threads calling
            # 'request_redraw' many times, resulting in 100% CPU.)
            if self._invalidated:
                return

            self._invalidated = True

            def redraw():
                self._invalidated = False
                self._redraw()

            self.eventloop.call_from_executor(redraw)

    def _redraw(self):
        """
        Render the command line again. (Not thread safe!)
        (From other threads, or if unsure, use `request_redraw`.)
        """
        # Only draw when no sub application was started.
        if self._sub_cli is None:
            self.renderer.render(self, self.layout, self.application.get_style(),
                                 is_done=self.is_done)

    def _on_resize(self):
        """
        When the window size changes, we erase the current output and request
        again the cursor position. When the CPR answer arrives, the output is
        drawn again.
        """
        # Erase, request position (when cursor is at the start position)
        # and redraw again. -- The order is important.
        self.renderer.erase()
        self.renderer.request_absolute_cursor_position()
        self._redraw()

    def run(self, reset_current_buffer=True, pre_run=None):
        """
        Read input from the command line.
        This runs the eventloop until a return value has been set.

        :param reset_current_buffer: Reset content of current buffer.
        :param pre_run: Callable that is called right after the reset has taken
            place. This allows custom initialisation.
        """
        assert pre_run is None or callable(pre_run)

        try:
            self._is_running = True

            self.application.on_start.fire(self)
            self.reset(reset_current_buffer=reset_current_buffer)

            # Call pre_run.
            if pre_run:
                pre_run()

            # Run eventloop in raw mode.
            with self.input.raw_mode():
                self.renderer.request_absolute_cursor_position()
                self._redraw()

                self.eventloop.run(self.input, self.create_eventloop_callbacks())
        finally:
            # Clean up renderer. (This will leave the alternate screen, if we use
            # that.)
            self.renderer.reset()
            self.application.on_stop.fire(self)
            self._is_running = False

        # Return result.
        return self.return_value()

    def run_async(self, reset_current_buffer=True, pre_run=None):
        """
        Same as `run`, but this returns a coroutine.

        This is mostly for Python >3.3, with asyncio.
        """
        assert pre_run is None or callable(pre_run)

        try:
            self._is_running = True

            self.application.on_start.fire(self)
            self.reset(reset_current_buffer=reset_current_buffer)

            # Call pre_run.
            if pre_run:
                pre_run()

            with self.input.raw_mode():
                self.renderer.request_absolute_cursor_position()
                self._redraw()

                g = self.eventloop.run_as_coroutine(
                        self.input, self.create_eventloop_callbacks())
                assert isinstance(g, GeneratorType)

                while True:
                    yield next(g)
        except StopIteration:
            raise StopIteration(self.return_value())
        finally:
            self.renderer.reset()
            self.application.on_stop.fire(self)
            self._is_running = False

    def run_sub_application(self, application, done_callback=None):
        """
        Run a sub `Application`.

        This will suspend the main application and display the sub application
        until that one returns a value. The value is returned by calling
        `done_callback` with the result.

        The sub application will share the same I/O of the main application.
        That means, it uses the same input and output channels and it shares
        the same event loop. [1]

        [1] Technically, it gets another Eventloop instance, but that is only a
            proxy to our main event loop. The reason is that calling 'stop'
            --which returns the result of an application when it's done-- is
            handled differently.
        """
        assert isinstance(application, Application)
        assert done_callback is None or callable(done_callback)

        if self._sub_cli is not None:
            raise RuntimeError('Another sub application started already.')

        # Erase current application.
        self.renderer.erase()

        # Callback when the sub app is done.
        def done():
            # Redraw sub app in done state.
            # and reset the renderer. (This reset will also quit the alternate
            # screen, if the sub application used that.)
            sub_cli._redraw()
            sub_cli.renderer.reset()

            self._sub_cli = None

            # Restore main application.
            self.renderer.request_absolute_cursor_position()
            self._redraw()

            # Deliver result.
            if done_callback:
                done_callback(sub_cli.return_value())

        # Create sub CommandLineInterface.
        sub_cli = CommandLineInterface(
            application=application,
            eventloop=_SubApplicationEventLoop(self, done),
            input=self.input,
            output=self.output)

        self._sub_cli = sub_cli

    def set_exit(self):
        """
        Set exit. When Control-D has been pressed.
        """
        on_exit = self.application.on_exit

        if on_exit != AbortAction.IGNORE:
            self._exit_flag = True
            self._redraw()

        if on_exit == AbortAction.RAISE_EXCEPTION:
            def eof_error():
                raise EOFError()
            self._set_return_callable(eof_error)

        elif on_exit == AbortAction.RETRY:
            self.reset()
            self.renderer.request_absolute_cursor_position()
            self.current_buffer.reset()

        elif on_exit == AbortAction.RETURN_NONE:
            self.set_return_value(None)

    def set_abort(self):
        """
        Set abort. When Control-C has been pressed.
        """
        on_abort = self.application.on_abort

        if on_abort != AbortAction.IGNORE:
            self._abort_flag = True
            self._redraw()

        if on_abort == AbortAction.RAISE_EXCEPTION:
            def keyboard_interrupt():
                raise KeyboardInterrupt()
            self._set_return_callable(keyboard_interrupt)

        elif on_abort == AbortAction.RETRY:
            self.reset()
            self.renderer.request_absolute_cursor_position()
            self.current_buffer.reset()

        elif on_abort == AbortAction.RETURN_NONE:
            self.set_return_value(None)

    def set_return_value(self, document):
        """
        Set a return value. The eventloop can retrieve the result it by calling
        `return_value`.
        """
        self._redraw()
        self._set_return_callable(lambda: document)

    def _set_return_callable(self, value):
        assert callable(value)
        self._return_value = value

        if self.eventloop:
            self.eventloop.stop()

    def run_in_terminal(self, func, render_cli_done=False):
        """
        Run function on the terminal above the prompt.

        What this does is first hiding the prompt, then running this callable
        (which can safely output to the terminal), and then again rendering the
        prompt which causes the output of this function to scroll above the
        prompt.

        :param func: The callable to execute.
        :param render_cli_done: When True, render the interface in the
                'Done' state first, then execute the function. If False,
                erase the interface first.

        :returns: the result of `func`.
        """
        # Draw interface in 'done' state, or erase.
        if render_cli_done:
            self._return_value = True
            self._redraw()
            self.renderer.reset()  # Make sure to disable mouse mode, etc...
        else:
            self.renderer.erase()

        # Run system command.
        with self.input.cooked_mode():
            result = func()
        self._return_value = None

        # Redraw interface again.
        self.renderer.reset()
        self.renderer.request_absolute_cursor_position()
        self._redraw()

        return result

    def run_system_command(self, command):
        """
        Run system command (While hiding the prompt. When finished, all the
        output will scroll above the prompt.)

        :param command: Shell command to be executed.
        """
        def run():
            if is_windows():
                os.system(command)  # Needs to be unicode for win32
            else:
                os.system(command.encode('utf-8'))

            try:
                six.moves.input('\nPress ENTER to continue...')
            except EOFError:
                pass

        self.run_in_terminal(run)

    def suspend_to_background(self):
        """
        (Not thread safe -- to be called from inside the key bindings.)
        Suspend process.
        """
        # Only suspend when the opperating system supports it.
        # (Not on Windows.)
        if hasattr(signal, 'SIGTSTP'):
            def run():
                # Send `SIGSTP` to own process.
                # This will cause it to suspend.
                os.kill(os.getpid(), signal.SIGTSTP)

            self.run_in_terminal(run)

    def print_tokens(self, tokens, style=None):
        """
        Print a list of (Token, text) tuples to the output.
        (When the UI is running, this method has to be called through
        `run_in_terminal`, otherwise it will destroy the UI.)

        :param style: Style class to use. Defaults to the active style in the CLI.
        """
        print_tokens(self.output, tokens, style or self.application.get_style())

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

    def return_value(self):
        """
        Get the return value. Not that this method can throw an exception.
        """
        # Note that it's a method, not a property, because it can throw
        # exceptions.
        if self._return_value:
            return self._return_value()

    @property
    def is_done(self):
        return self.is_exiting or self.is_aborting or self.is_returning

    def _create_async_completer(self, buffer):
        """
        Create function for asynchronous autocompletion.
        (Autocomplete in other thread.)
        """
        complete_thread_running = [False]  # By ref.

        def async_completer(select_first=False, select_last=False,
                            insert_common_part=False, complete_event=None):
            document = buffer.document
            complete_event = complete_event or CompleteEvent(text_inserted=True)

            # Don't start two threads at the same time.
            if complete_thread_running[0]:
                return

            # Don't complete when we already have completions.
            if buffer.complete_state or not buffer.completer:
                return

            # Otherwise, get completions in other thread.
            complete_thread_running[0] = True

            def run():
                completions = list(buffer.completer.get_completions(document, complete_event))
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

                        set_completions = True
                        select_first_anyway = False

                        # When the commond part has to be inserted, and there
                        # is a common part.
                        if insert_common_part:
                            common_part = get_common_complete_suffix(document, completions)
                            if common_part:
                                # Insert + run completer again.
                                buffer.insert_text(common_part)
                                async_completer()
                                set_completions = False
                            else:
                                # When we were asked to insert the "common"
                                # prefix, but there was no common suffix but
                                # still exactly one match, then select the
                                # first. (It could be that we have a completion
                                # which does * expension, like '*.py', with
                                # exactly one match.)
                                if len(completions) == 1:
                                    select_first_anyway = True

                        if set_completions:
                            buffer.set_completions(
                                completions=completions,
                                go_to_first=select_first or select_first_anyway,
                                go_to_last=select_last)
                        self._redraw()
                    else:
                        # Otherwise, restart thread.
                        async_completer()

                if self.eventloop:
                    self.eventloop.call_from_executor(callback)

            self.eventloop.run_in_executor(run)
        return async_completer

    def _create_auto_suggest_function(self, buffer):
        """
        Create function for asynchronous auto suggestion.
        (AutoSuggest in other thread.)
        """
        suggest_thread_running = [False]  # By ref.

        def async_suggestor():
            document = buffer.document

            # Don't start two threads at the same time.
            if suggest_thread_running[0]:
                return

            # Don't suggest when we already have a suggestion.
            if buffer.suggestion or not buffer.auto_suggest:
                return

            # Otherwise, get completions in other thread.
            suggest_thread_running[0] = True

            def run():
                suggestion = buffer.auto_suggest.get_suggestion(self, buffer, document)
                suggest_thread_running[0] = False

                def callback():
                    # Set suggestion only if the text was not yet changed.
                    if buffer.text == document.text and \
                            buffer.cursor_position == document.cursor_position:

                        # Set suggestion and redraw interface.
                        buffer.suggestion = suggestion
                        self._redraw()
                    else:
                        # Otherwise, restart thread.
                        async_suggestor()

                if self.eventloop:
                    self.eventloop.call_from_executor(callback)

            self.eventloop.run_in_executor(run)
        return async_suggestor

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

    def create_eventloop_callbacks(self):
        return _InterfaceEventLoopCallbacks(self)


class _InterfaceEventLoopCallbacks(EventLoopCallbacks):
    """
    Callbacks on the ``CommandLineInterface`` object, to which an eventloop can
    talk.
    """
    def __init__(self, cli):
        assert isinstance(cli, CommandLineInterface)
        self.cli = cli

    @property
    def _active_cli(self):
        """
        Return the active `CommandLineInterface`.
        """
        cli = self.cli

        # If there is a sub CLI. That one is always active.
        while cli._sub_cli:
            cli = cli._sub_cli

        return cli

    def terminal_size_changed(self):
        """
        Report terminal size change. This will trigger a redraw.
        """
        self._active_cli._on_resize()

    def input_timeout(self):
        cli = self._active_cli
        cli.application.on_input_timeout.fire(cli)

    def feed_key(self, key_press):
        """
        Feed a key press to the CommandLineInterface.
        """
        # Feed the key and redraw.
        self._active_cli.input_processor.feed_key(key_press)

    def redraw(self):
        """
        Redraw the interface. (Should probably be called after each
        `feed_key`.)
        """
        self._active_cli._redraw()


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
        self._lock = threading.RLock()
        self._cli = cli
        self._buffer = []

        self.errors = sys.__stdout__.errors
        self.encoding = sys.__stdout__.encoding

    def _do(self, func):
        if self._cli._is_running:
            run_in_terminal = functools.partial(self._cli.run_in_terminal, func)
            self._cli.eventloop.call_from_executor(run_in_terminal)
        else:
            func()

    def _write(self, data):
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
                    self._cli.output.write(s)
            self._do(run)
        else:
            # Otherwise, cache in buffer.
            self._buffer.append(data)

    def write(self, data):
        with self._lock:
            self._write(data)

    def _flush(self):
        def run():
            for s in self._buffer:
                self._cli.output.write(s)
            self._buffer = []
            self._cli.output.flush()
        self._do(run)

    def flush(self):
        """
        Flush buffered output.
        """
        with self._lock:
            self._flush()


class _SubApplicationEventLoop(EventLoop):
    """
    Eventloop used by sub applications.

    A sub application is an `Application` that is "spawned" by a parent
    application. The parent application is suspended temporarily and the sub
    application is displayed instead.

    It doesn't need it's own event loop. The `EventLoopCallbacks` from the
    parent application are redirected to the sub application. So if the event
    loop that is run by the parent application detects input, the callbacks
    will make sure that it's forwarded to the sub application.

    When the sub application has a return value set, it will terminate
    by calling the `stop` method of this event loop. This is used to
    transfer control back to the parent application.
    """
    def __init__(self, cli, stop_callback):
        assert isinstance(cli, CommandLineInterface)
        assert callable(stop_callback)

        self.cli = cli
        self.stop_callback = stop_callback

    def stop(self):
        self.stop_callback()

    def close(self):
        pass

    def run_in_executor(self, callback):
        self.cli.run_in_executor(callback)

    def call_from_executor(self, callback):
        self.cli.call_from_executor(callback)
