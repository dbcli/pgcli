from __future__ import unicode_literals

from .buffer import Buffer
from .cache import SimpleCache
from .clipboard import Clipboard, InMemoryClipboard
from .enums import EditingMode
from .eventloop import EventLoop, get_event_loop
from .filters import AppFilter, to_app_filter
from .filters import Condition
from .input.base import Input
from .input.defaults import create_input
from .key_binding.defaults import load_key_bindings
from .key_binding.key_processor import KeyProcessor
from .key_binding.key_bindings import KeyBindings, KeyBindingsBase, merge_key_bindings, ConditionalKeyBindings
from .key_binding.vi_state import ViState
from .keys import Keys
from .layout.layout import Layout
from .layout.controls import BufferControl
from .output import Output
from .output.defaults import create_output
from .renderer import Renderer, print_text_fragments
from .search_state import SearchState
from .styles import BaseStyle, default_style
from .utils import Event

from subprocess import Popen
import functools
import os
import signal
import six
import sys
import textwrap
import threading
import time
import types
import weakref

__all__ = (
    'Application',
)


class Application(object):
    """
    The main Application class!
    This glues everything together.

    :param layout: A :class:`~prompt_toolkit.layout.layout.Layout` instance.
    :param key_bindings:
        :class:`~prompt_toolkit.key_binding.key_bindings.KeyBindingsBase` instance for
        the key bindings.
    :param clipboard: :class:`~prompt_toolkit.clipboard.base.Clipboard` to use.
    :param on_abort: What to do when Control-C is pressed.
    :param on_exit: What to do when Control-D is pressed.
    :param full_screen: When True, run the application on the alternate screen buffer.
    :param get_title: Callable that returns the current title to be displayed in the terminal.
    :param erase_when_done: (bool) Clear the application output when it finishes.
    :param reverse_vi_search_direction: Normally, in Vi mode, a '/' searches
        forward and a '?' searches backward. In readline mode, this is usually
        reversed.

    Filters:

    :param mouse_support: (:class:`~prompt_toolkit.filters.AppFilter` or
        boolean). When True, enable mouse support.
    :param paste_mode: :class:`~prompt_toolkit.filters.AppFilter` or boolean.
    :param editing_mode: :class:`~prompt_toolkit.enums.EditingMode`.

    Callbacks (all of these should accept a
    :class:`~prompt_toolkit.application.Application` object as input.)

    :param on_reset: Called during reset.
    :param on_render: Called right after rendering.
    :param on_invalidate: Called when the UI has been invalidated.

    I/O:

    :param eventloop: The :class:`~prompt_toolkit.eventloop.base.EventLoop` to
                      be used when `run` is called. The easiest way to create
                      an eventloop is by calling
                      :meth:`~prompt_toolkit.shortcuts.create_eventloop`.
    :param input: :class:`~prompt_toolkit.input.Input` instance.
    :param output: :class:`~prompt_toolkit.output.Output` instance. (Probably
                   Vt100_Output or Win32Output.)
    """
    def __init__(self, layout=None,
                 style=None,
                 key_bindings=None, clipboard=None,
                 full_screen=False, mouse_support=False,
                 get_title=None,

                 paste_mode=False,
                 editing_mode=EditingMode.EMACS,
                 erase_when_done=False,
                 reverse_vi_search_direction=False,

                 on_reset=None, on_render=None, on_invalidate=None,

                 # I/O.
                 loop=None, input=None, output=None):

        paste_mode = to_app_filter(paste_mode)
        mouse_support = to_app_filter(mouse_support)
        reverse_vi_search_direction = to_app_filter(reverse_vi_search_direction)

        assert isinstance(layout, Layout)
        assert key_bindings is None or isinstance(key_bindings, KeyBindingsBase)
        assert clipboard is None or isinstance(clipboard, Clipboard)
        assert isinstance(full_screen, bool)
        assert get_title is None or callable(get_title)
        assert isinstance(paste_mode, AppFilter)
        assert isinstance(editing_mode, six.string_types)
        assert style is None or isinstance(style, BaseStyle)
        assert isinstance(erase_when_done, bool)

        assert on_reset is None or callable(on_reset)
        assert on_render is None or callable(on_render)
        assert on_invalidate is None or callable(on_invalidate)

        assert loop is None or isinstance(loop, EventLoop)
        assert output is None or isinstance(output, Output)
        assert input is None or isinstance(input, Input)

        self.style = style or default_style()

        if key_bindings is None:
            key_bindings = load_key_bindings()

        if get_title is None:
            get_title = lambda: None

        self.layout = layout
        self.key_bindings = key_bindings
        self.clipboard = clipboard or InMemoryClipboard()
        self.full_screen = full_screen
        self.mouse_support = mouse_support
        self.get_title = get_title

        self.paste_mode = paste_mode
        self.editing_mode = editing_mode
        self.erase_when_done = erase_when_done
        self.reverse_vi_search_direction = reverse_vi_search_direction

        # Events.
        self.on_invalidate = Event(self, on_invalidate)
        self.on_render = Event(self, on_render)
        self.on_reset = Event(self, on_reset)

        # I/O.
        self.loop = loop or get_event_loop()
        self.output = output or create_output()
        self.input = input or create_input(sys.stdin)

        # List of 'extra' functions to execute before a Application.run.
        self.pre_run_callables = []

        self._is_running = False
        self.future = None

        #: Quoted insert. This flag is set if we go into quoted insert mode.
        self.quoted_insert = False

        #: Vi state. (For Vi key bindings.)
        self.vi_state = ViState()

        #: When to flush the input (For flushing escape keys.) This is important
        #: on terminals that use vt100 input. We can't distinguish the escape
        #: key from for instance the left-arrow key, if we don't know what follows
        #: after "\x1b". This little timer will consider "\x1b" to be escape if
        #: nothing did follow in this time span.
        self.input_timeout = .5

        #: The `Renderer` instance.
        # Make sure that the same stdout is used, when a custom renderer has been passed.
        self.renderer = Renderer(
            self.style,
            self.output,
            full_screen=full_screen,
            mouse_support=mouse_support)

        #: Render counter. This one is increased every time the UI is rendered.
        #: It can be used as a key for caching certain information during one
        #: rendering.
        self.render_counter = 0

        #: List of which user controls have been painted to the screen. (The
        #: visible controls.)
        self.rendered_user_controls = []

        #: When there is high CPU, postpone the rendering max x seconds.
        #: '0' means: don't postpone. '.5' means: try to draw at least twice a second.
        self.max_render_postpone_time = 0  # E.g. .5

        # Invalidate flag. When 'True', a repaint has been scheduled.
        self._invalidated = False
        self._invalidate_events = []  # Collection of 'invalidate' Event objects.

        #: The `InputProcessor` instance.
        self.key_processor = KeyProcessor(_CombinedRegistry(self), weakref.ref(self))

        # Pointer to child Application. (In chain of Application instances.)
        self._child_app = None  # None or other Application instance.

        # Trigger initialize callback.
        self.reset()

    @property
    def current_buffer(self):
        """
        The currently focussed :class:`~.Buffer`.

        (This returns a dummy :class:`.Buffer` when none of the actual buffers
        has the focus. In this case, it's really not practical to check for
        `None` values or catch exceptions every time.)
        """
        return self.layout.current_buffer or Buffer(loop=self.loop)  # Dummy buffer.

    @property
    def current_search_state(self):
        """
        Return the current `SearchState`. (The one for the focussed
        `BufferControl`.)
        """
        ui_control = self.layout.current_control
        if isinstance(ui_control, BufferControl):
            return ui_control.search_state
        else:
            return SearchState()  # Dummy search state.  (Don't return None!)

    @property
    def visible_windows(self):
        """
        Return a list of `Window` objects that represent visible user controls.
        """
        last_screen = self.renderer.last_rendered_screen
        if last_screen is not None:
            return last_screen.visible_windows
        else:
            return []

    @property
    def focussable_windows(self):
        """
        Return a list of `Window` objects that are focussable.
        """
        return [w for w in self.visible_windows if w.content.is_focussable(self)]

    @property
    def terminal_title(self):
        """
        Return the current title to be displayed in the terminal.
        When this in `None`, the terminal title remains the original.
        """
        result = self.get_title()

        # Make sure that this function returns a unicode object,
        # and not a byte string.
        assert result is None or isinstance(result, six.text_type)
        return result

    def reset(self):
        """
        Reset everything, for reading the next input.
        """
        # Notice that we don't reset the buffers. (This happens just before
        # returning, and when we have multiple buffers, we clearly want the
        # content in the other buffers to remain unchanged between several
        # calls of `run`. (And the same is true for the focus stack.)

        self._exit_flag = False
        self._abort_flag = False

        self.renderer.reset()
        self.key_processor.reset()
        self.layout.reset()
        self.vi_state.reset()

        # Trigger reset event.
        self.on_reset.fire()

        # Make sure that we have a 'focussable' widget focussed.
        # (The `Layout` class can't determine this.)
        layout = self.layout

        if not layout.current_control.is_focussable(self):
            for w in layout.find_all_windows():
                if w.content.is_focussable(self):
                    layout.current_window = w
                    break

    def invalidate(self):
        """
        Thread safe way of sending a repaint trigger to the input event loop.
        """
        # Never schedule a second redraw, when a previous one has not yet been
        # executed. (This should protect against other threads calling
        # 'invalidate' many times, resulting in 100% CPU.)
        if self._invalidated:
            return
        else:
            self._invalidated = True

        # Trigger event.
        self.on_invalidate.fire()

        if self.loop is not None:
            def redraw():
                self._invalidated = False
                self._redraw()

            # Call redraw in the eventloop (thread safe).
            # Usually with the high priority, in order to make the application
            # feel responsive, but this can be tuned by changing the value of
            # `max_render_postpone_time`.
            if self.max_render_postpone_time:
                _max_postpone_until = time.time() + self.max_render_postpone_time
            else:
                _max_postpone_until = None

            self.loop.call_from_executor(
                redraw, _max_postpone_until=_max_postpone_until)

    def _redraw(self, render_as_done=False):
        """
        Render the command line again. (Not thread safe!) (From other threads,
        or if unsure, use :meth:`.Application.invalidate`.)

        :param render_as_done: make sure to put the cursor after the UI.
        """
        # Only draw when no sub application was started.
        if self._is_running and self._child_app is None:
            # Clear the 'rendered_ui_controls' list. (The `Window` class will
            # populate this during the next rendering.)
            self.rendered_user_controls = []

            # Render
            self.render_counter += 1

            if render_as_done:
                if self.erase_when_done:
                    self.renderer.erase()
                else:
                    # Draw in 'done' state and reset renderer.
                    self.renderer.render(self, self.layout, is_done=render_as_done)
            else:
                self.renderer.render(self, self.layout)

            # Fire render event.
            self.on_render.fire()

            self._update_invalidate_events()

    def _update_invalidate_events(self):
        """
        Make sure to attach 'invalidate' handlers to all invalidate events in
        the UI.
        """
        # Remove all the original event handlers. (Components can be removed
        # from the UI.)
        for ev in self._invalidate_events:
            ev -= self.invalidate

        # Gather all new events.
        # (All controls are able to invalidate themself.)
        def gather_events():
            for c in self.layout.find_all_controls():
                for ev in c.get_invalidate_events():
                    yield ev

        self._invalidate_events = list(gather_events())

        # Attach invalidate event handler.
        invalidate = lambda sender: self.invalidate()

        for ev in self._invalidate_events:
            ev += invalidate

    def _on_resize(self):
        """
        When the window size changes, we erase the current output and request
        again the cursor position. When the CPR answer arrives, the output is
        drawn again.
        """
        # Erase, request position (when cursor is at the start position)
        # and redraw again. -- The order is important.
        self.renderer.erase(leave_alternate_screen=False, erase_title=False)
        self.renderer.request_absolute_cursor_position()
        self._redraw()

    def _pre_run(self, pre_run=None):
        " Called during `run`. "
        if pre_run:
            pre_run()

        # Process registered "pre_run_callables" and clear list.
        for c in self.pre_run_callables:
            c()
        del self.pre_run_callables[:]

    def start(self, pre_run=None):
        """
        Start running the UI.
        This returns a `Future`. You're supposed to call the
        `run_until_complete` function of the event loop to actually run the UI.

        :returns: A :class:`prompt_toolkit.eventloop.future.Future` object.
        """
        f, done_cb = self._start(pre_run=pre_run)
        return f

    def _start(self, pre_run=None):
        " Like `start`, but also returns the `done()` callback. "
        assert not self._is_running
        self._is_running = True

        loop = self.loop
        f = loop.create_future()
        self.future = f  # XXX: make sure to set this before calling '_redraw'.

        # Reset.
        self.reset()
        self._pre_run(pre_run)

        # Enter raw mode.
        raw_mode = self.input.raw_mode()
        raw_mode.__enter__()

        # Draw UI.
        self.renderer.request_absolute_cursor_position()
        self._redraw()

        def feed_keys(keys):
            self.key_processor.feed_multiple(keys)
            self.key_processor.process_keys()

        def read_from_input():
            # Get keys from the input object.
            keys = self.input.read_keys()

            # Feed to key processor.
            self.key_processor.feed_multiple(keys)
            self.key_processor.process_keys()

            # Quit when the input stream was closed.
            if self.input.closed:
            	f.set_exception(EOFError)
            else:
                # Automatically flush keys.
                # (_daemon needs to be set, otherwise, this will hang the
                # application for .5 seconds before exiting.)
                loop.run_in_executor(auto_flush_input, _daemon=True)

        def auto_flush_input():
            # Flush input after timeout.
            # (Used for flushing the enter key.)
            time.sleep(self.input_timeout)
            loop.call_from_executor(flush_input)

        def flush_input():
            if not self.is_done:
                # Get keys, and feed to key processor.
                keys = self.input.flush_keys()
                self.key_processor.feed_multiple(keys)
                self.key_processor.process_keys()

                if self.input.closed:
                    f.set_exception(EOFError)

        # Set event loop handlers.
        previous_input, previous_cb = loop.set_input(self.input, read_from_input)

        has_sigwinch = hasattr(signal, 'SIGWINCH')
        if has_sigwinch:
            previous_winch_handler = loop.add_signal_handler(
                signal.SIGWINCH, self._on_resize)

        def done():
            try:
                # Render UI in 'done' state.
                raw_mode.__exit__(None, None, None)
                self._redraw(render_as_done=True)
                self.renderer.reset()

                # Clear event loop handlers.
                if previous_input:
                    loop.set_input(previous_input, previous_cb)

                if has_sigwinch:
                    loop.add_signal_handler(signal.SIGWINCH, previous_winch_handler)
            finally:
                self._is_running = False

        f.add_done_callback(lambda _: done())
        return f, done

    def run(self, pre_run=None):
        """
        A blocking 'run' call that waits until the UI is finished.
        """
        f, done_cb = self._start(pre_run=pre_run)
        try:
            self.loop.run_until_complete(f)
            return f.result()
        finally:
            # Make sure that the 'done' callback from the 'start' function has
            # been called. If something bad happens in the event loop, and an
            # exception was raised, then we can end up at this point without
            # having 'f' in the 'done' state.
            if not f.done():
                done_cb()
            assert not self._is_running

    try:
        six.exec_(textwrap.dedent('''
    async def run_async(self, pre_run=None):
        """
        Like `run`, but this is a coroutine.
        (For use with an asyncio event loop.)
        """
        f = self.start(pre_run=pre_run)
        await self.loop.run_as_coroutine(f)
        return f.result()
    '''), globals(), locals())
    except SyntaxError:
        def run_async(self, pre_run=None):
            raise NotImplementedError('`run_async` requires at least Python 3.5.')

    def run_sub_application(self, application, _from_application_generator=False):
        """
        Run a sub :class:`~prompt_toolkit.application.Application`.

        This will suspend the main application and display the sub application
        until that one returns a value. A future that will contain the result
        will be returned.

        The sub application will share the same I/O of the main application.
        That means, it uses the same input and output channels and it shares
        the same event loop.

        .. note:: Technically, it gets another Eventloop instance, but that is
            only a proxy to our main event loop. The reason is that calling
            'stop' --which returns the result of an application when it's
            done-- is handled differently.
        """
        assert isinstance(application, Application)
        assert isinstance(_from_application_generator, bool)

        assert application.loop == self.loop
        application.input = self.input
        application.output = self.output

        if self._child_app is not None:
            raise RuntimeError('Another sub application started already.')

        # Erase current application.
        if not _from_application_generator:
            self.renderer.erase()

        # Callback when the sub app is done.
        def done(_):
            self._child_app = None

            # Redraw sub app in done state.
            # and reset the renderer. (This reset will also quit the alternate
            # screen, if the sub application used that.)
            application._redraw(render_as_done=True)
            application.renderer.reset()
            application._is_running = False  # Don't render anymore.

            # Restore main application.
            if not _from_application_generator:
                self.renderer.request_absolute_cursor_position()
                self._redraw()

        # Allow rendering of sub app.
        future = application.start()
        future.add_done_callback(done)

        application._redraw()
        self._child_app = application

        return future

    def exit(self):
        " Set exit. When Control-D has been pressed. "
        self._exit_flag = True
        self.future.set_exception(EOFError)

    def abort(self):
        " Set abort. When Control-C has been pressed. "
        self._abort_flag = True
        self.future.set_exception(KeyboardInterrupt)

    def set_return_value(self, value):
        """
        Set a return value. The eventloop can retrieve the result it by calling
        `return_value`.
        """
        self.future.set_result(value)

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
            self._redraw(render_as_done=True)
        else:
            self.renderer.erase()

        # Run system command.
        with self.input.cooked_mode():
            result = func()

        # Redraw interface again.
        self.renderer.reset()
        self.renderer.request_absolute_cursor_position()
        self._redraw()

        return result

    def run_application_generator(self, coroutine, render_cli_done=False):
        """
        EXPERIMENTAL
        Like `run_in_terminal`, but takes a generator that can yield Application instances.

        Example:

            def gen():
                yield Application1(...)
                print('...')
                yield Application2(...)
            app.run_application_generator(gen)

        The values which are yielded by the given coroutine are supposed to be
        `Application` instances that run in the current CLI, all other code is
        supposed to be CPU bound, so except for yielding the applications,
        there should not be any user interaction or I/O in the given function.
        """
        # Draw interface in 'done' state, or erase.
        if render_cli_done:
            self._redraw(render_as_done=True)
        else:
            self.renderer.erase()

        # Loop through the generator.
        g = coroutine()
        assert isinstance(g, types.GeneratorType)

        def step_next(f=None):
            " Execute next step of the coroutine."
            try:
                # Run until next yield, in cooked mode.
                with self.input.cooked_mode():
                    if f is None:
                        result = g.send(None)
                    else:
                        exc = f.exception()
                        if exc:
                            result = g.throw(exc)
                        else:
                            result = g.send(f.result())
            except StopIteration:
                done()
            except:
                done()
                raise
            else:
                # Process yielded value from coroutine.
                assert isinstance(result, Application)
                f = self.run_sub_application(result, _from_application_generator=True)
                f.add_done_callback(lambda _: step_next(f))

        def done():
            # Redraw interface again.
            self.renderer.reset()
            self.renderer.request_absolute_cursor_position()
            self._redraw()

        # Start processing coroutine.
        step_next()

    def run_system_command(self, command):
        """
        Run system command (While hiding the prompt. When finished, all the
        output will scroll above the prompt.)

        :param command: Shell command to be executed.
        """
        def wait_for_enter():
            """
            Create a sub application to wait for the enter key press.
            This has two advantages over using 'input'/'raw_input':
            - This will share the same input/output I/O.
            - This doesn't block the event loop.
            """
            from .shortcuts import Prompt

            key_bindings = KeyBindings()

            @key_bindings.add(Keys.ControlJ)
            @key_bindings.add(Keys.ControlM)
            def _(event):
                event.app.set_return_value(None)

            prompt = Prompt(
                message='Press ENTER to continue...',
                loop=self.loop,
                extra_key_bindings=key_bindings,
                include_default_key_bindings=False)
            self.run_sub_application(prompt.app)

        def run():
            # Try to use the same input/output file descriptors as the one,
            # used to run this application.
            try:
                input_fd = self.input.fileno()
            except AttributeError:
                input_fd = sys.stdin.fileno()
            try:
                output_fd = self.output.fileno()
            except AttributeError:
                output_fd = sys.stdout.fileno()

            # Run sub process.
            # XXX: This will still block the event loop.
            p = Popen(command, shell=True,
                      stdin=input_fd, stdout=output_fd)
            p.wait()

            # Wait for the user to press enter.
            wait_for_enter()

        self.run_in_terminal(run)

    def suspend_to_background(self, suspend_group=True):
        """
        (Not thread safe -- to be called from inside the key bindings.)
        Suspend process.

        :param suspend_group: When true, suspend the whole process group.
            (This is the default, and probably what you want.)
        """
        # Only suspend when the opperating system supports it.
        # (Not on Windows.)
        if hasattr(signal, 'SIGTSTP'):
            def run():
                # Send `SIGSTP` to own process.
                # This will cause it to suspend.

                # Usually we want the whole process group to be suspended. This
                # handles the case when input is piped from another process.
                if suspend_group:
                    os.kill(0, signal.SIGTSTP)
                else:
                    os.kill(os.getpid(), signal.SIGTSTP)

            self.run_in_terminal(run)

    def print_text_fragments(self, text_fragments, style=None):
        """
        Print a list of (style_str, text) tuples to the output.
        (When the UI is running, this method has to be called through
        `run_in_terminal`, otherwise it will destroy the UI.)

        :param text_fragments: List of ``(style_str, text)`` tuples.
        :param style: Style class to use. Defaults to the active style in the CLI.
        """
        print_text_fragments(self.output, text_fragments, style or self.style)

    @property
    def is_exiting(self):
        " ``True`` when the exit flag as been set. "
        return self._exit_flag

    @property
    def is_aborting(self):
        " ``True`` when the abort flag as been set. "
        return self._abort_flag

    @property
    def is_done(self):
        return self.future and self.future.done()

    def stdout_proxy(self, raw=False):
        """
        Create an :class:`_StdoutProxy` class which can be used as a patch for
        `sys.stdout`. Writing to this proxy will make sure that the text
        appears above the prompt, and that it doesn't destroy the output from
        the renderer.

        :param raw: (`bool`) When True, vt100 terminal escape sequences are not
                    removed/escaped.
        """
        return _StdoutProxy(self, raw=raw)

    def patch_stdout_context(self, raw=False, patch_stdout=True, patch_stderr=True):
        """
        Return a context manager that will replace ``sys.stdout`` with a proxy
        that makes sure that all printed text will appear above the prompt, and
        that it doesn't destroy the output from the renderer.

        :param patch_stdout: Replace `sys.stdout`.
        :param patch_stderr: Replace `sys.stderr`.
        """
        return _PatchStdoutContext(
            self.stdout_proxy(raw=raw),
            patch_stdout=patch_stdout, patch_stderr=patch_stderr)


class _PatchStdoutContext(object):
    def __init__(self, new_stdout, patch_stdout=True, patch_stderr=True):
        self.new_stdout = new_stdout
        self.patch_stdout = patch_stdout
        self.patch_stderr = patch_stderr

    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        if self.patch_stdout:
            sys.stdout = self.new_stdout
        if self.patch_stderr:
            sys.stderr = self.new_stdout

    def __exit__(self, *a, **kw):
        if self.patch_stdout:
            sys.stdout = self.original_stdout

        if self.patch_stderr:
            sys.stderr = self.original_stderr


class _StdoutProxy(object):
    """
    Proxy for stdout, as returned by
    :class:`Application.stdout_proxy`.
    """
    def __init__(self, app, raw=False):
        assert isinstance(app, Application)
        assert isinstance(raw, bool)

        self._lock = threading.RLock()
        self._cli = app
        self._raw = raw
        self._buffer = []

        self.errors = sys.__stdout__.errors
        self.encoding = sys.__stdout__.encoding

    def _do(self, func):
        if self._cli._is_running:
            run_in_terminal = functools.partial(self._cli.run_in_terminal, func)
            self._cli.loop.call_from_executor(run_in_terminal)
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
                    if self._raw:
                        self._cli.output.write_raw(s)
                    else:
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
                if self._raw:
                    self._cli.output.write_raw(s)
                else:
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


class _CombinedRegistry(KeyBindingsBase):
    """
    The `KeyBindings` of key bindings for a `Application`.
    This merges the global key bindings with the one of the current user
    control.
    """
    def __init__(self, app):
        self.app = app
        self._cache = SimpleCache()

    @property
    def _version(self):
        """ Not needed - this object is not going to be wrapped in another
        KeyBindings object. """
        raise NotImplementedError

    def _create_key_bindings(self, current_control, other_controls):
        """
        Create a `KeyBindings` object that merges the `KeyBindings` from the
        `UIControl` with the other user controls and the global key bindings.
        """
        # Collect global key bindings of other visible user controls.
        key_bindings = [c.get_key_bindings(self.app) for c in other_controls]
        key_bindings = [b.global_key_bindings for b in key_bindings
                        if b and b.global_key_bindings]

        others_key_bindings = merge_key_bindings(
            [self.app.key_bindings] + key_bindings)

        ui_key_bindings = current_control.get_key_bindings(self.app)

        if ui_key_bindings is None:
            # No bindings for this user control. Just return everything else.
            return others_key_bindings
        else:
            # Bindings for this user control found.
            # Keep the 'modal' parameter into account.
            @Condition
            def is_not_modal(app):
                return not ui_key_bindings.modal

            return merge_key_bindings([
                ConditionalKeyBindings(others_key_bindings, is_not_modal),
                ui_key_bindings.key_bindings or KeyBindings(),
            ])

    @property
    def _key_bindings(self):
        current_control = self.app.layout.current_control
        other_controls = list(self.app.layout.find_all_controls())
        key = current_control, frozenset(other_controls)

        return self._cache.get(
            key, lambda: self._create_key_bindings(current_control, other_controls))

    def get_bindings_for_keys(self, keys):
        return self._key_bindings.get_bindings_for_keys(keys)

    def get_bindings_starting_with_keys(self, keys):
        return self._key_bindings.get_bindings_starting_with_keys(keys)
