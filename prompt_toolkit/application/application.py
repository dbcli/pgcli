from __future__ import unicode_literals

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.cache import SimpleCache
from prompt_toolkit.clipboard import Clipboard, InMemoryClipboard
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.eventloop import get_event_loop, ensure_future, Return, run_in_executor, run_until_complete, call_from_executor, From, Future
from prompt_toolkit.filters import to_filter
from prompt_toolkit.input.base import Input
from prompt_toolkit.input.defaults import create_input
from prompt_toolkit.input.typeahead import store_typeahead, get_typeahead
from prompt_toolkit.key_binding.bindings.mouse import load_mouse_bindings
from prompt_toolkit.key_binding.bindings.page_navigation import load_page_navigation_bindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, ConditionalKeyBindings, KeyBindingsBase, merge_key_bindings
from prompt_toolkit.key_binding.key_processor import KeyProcessor
from prompt_toolkit.key_binding.vi_state import ViState
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import Output
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.renderer import Renderer, print_formatted_text
from prompt_toolkit.search_state import SearchState
from prompt_toolkit.styles import BaseStyle, default_style, merge_styles, DynamicStyle
from prompt_toolkit.utils import Event
from .current import set_app

from subprocess import Popen
import os
import signal
import six
import sys
import time

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

    :param mouse_support: (:class:`~prompt_toolkit.filters.Filter` or
        boolean). When True, enable mouse support.
    :param paste_mode: :class:`~prompt_toolkit.filters.Filter` or boolean.
    :param editing_mode: :class:`~prompt_toolkit.enums.EditingMode`.

    :param enable_page_navigation_bindings: When `True`, enable the page
        navigation key bindings. These include both Emacs and Vi bindings like
        page-up, page-down and so on to scroll through pages. Mostly useful for
        creating an editor. Probably, you don't want this for the
        implementation of a REPL.

    Callbacks (all of these should accept a
    :class:`~prompt_toolkit.application.Application` object as input.)

    :param on_reset: Called during reset.
    :param on_render: Called right after rendering.
    :param on_invalidate: Called when the UI has been invalidated.

    I/O:

    :param input: :class:`~prompt_toolkit.input.Input` instance.
    :param output: :class:`~prompt_toolkit.output.Output` instance. (Probably
                   Vt100_Output or Win32Output.)
    """
    def __init__(self, layout=None,
                 style=None,
                 key_bindings=None, clipboard=None,
                 full_screen=False, mouse_support=False,
                 enable_page_navigation_bindings=False,
                 get_title=None,

                 paste_mode=False,
                 editing_mode=EditingMode.EMACS,
                 erase_when_done=False,
                 reverse_vi_search_direction=False,

                 on_reset=None, on_render=None, on_invalidate=None,

                 # I/O.
                 input=None, output=None):

        paste_mode = to_filter(paste_mode)
        mouse_support = to_filter(mouse_support)
        reverse_vi_search_direction = to_filter(reverse_vi_search_direction)
        enable_page_navigation_bindings = to_filter(enable_page_navigation_bindings)

        assert isinstance(layout, Layout)
        assert key_bindings is None or isinstance(key_bindings, KeyBindingsBase)
        assert clipboard is None or isinstance(clipboard, Clipboard)
        assert isinstance(full_screen, bool)
        assert get_title is None or callable(get_title)
        assert isinstance(editing_mode, six.string_types)
        assert style is None or isinstance(style, BaseStyle)
        assert isinstance(erase_when_done, bool)

        assert on_reset is None or callable(on_reset)
        assert on_render is None or callable(on_render)
        assert on_invalidate is None or callable(on_invalidate)

        assert output is None or isinstance(output, Output)
        assert input is None or isinstance(input, Input)

        self.style = style

        if get_title is None:
            get_title = lambda: None


        # Key bindings.
        self.key_bindings = key_bindings
        self._default_bindings = load_key_bindings()
        self._page_navigation_bindings = load_page_navigation_bindings()
        self._mouse_bindings = load_mouse_bindings()

        self.layout = layout
        self.clipboard = clipboard or InMemoryClipboard()
        self.full_screen = full_screen
        self.mouse_support = mouse_support
        self.get_title = get_title

        self.paste_mode = paste_mode
        self.editing_mode = editing_mode
        self.erase_when_done = erase_when_done
        self.reverse_vi_search_direction = reverse_vi_search_direction
        self.enable_page_navigation_bindings = enable_page_navigation_bindings

        # Events.
        self.on_invalidate = Event(self, on_invalidate)
        self.on_render = Event(self, on_render)
        self.on_reset = Event(self, on_reset)

        # I/O.
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
            merge_styles([
                default_style(),
                DynamicStyle(lambda: self.style),
            ]),
            self.output,
            full_screen=full_screen,
            mouse_support=mouse_support)

        #: Render counter. This one is increased every time the UI is rendered.
        #: It can be used as a key for caching certain information during one
        #: rendering.
        self.render_counter = 0

        #: When there is high CPU, postpone the rendering max x seconds.
        #: '0' means: don't postpone. '.5' means: try to draw at least twice a second.
        self.max_render_postpone_time = 0  # E.g. .5

        # Invalidate flag. When 'True', a repaint has been scheduled.
        self._invalidated = False
        self._invalidate_events = []  # Collection of 'invalidate' Event objects.

        #: The `InputProcessor` instance.
        self.key_processor = KeyProcessor(_CombinedRegistry(self))

        # If `run_in_terminal` was called. This will point to a `Future` what will be
        # set at the point whene the previous run finishes.
        self._running_in_terminal = False
        self._running_in_terminal_f = get_event_loop().create_future()
        self._running_in_terminal_f.set_result(None)

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
        return self.layout.current_buffer or Buffer()  # Dummy buffer.

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
        # Focussable windows are windows that are visible, but also part of the modal container.
        # Make sure to keep the ordering.
        visible_windows = self.visible_windows
        return [w for w in self.layout.get_focussable_windows() if w in visible_windows]

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

        if not layout.current_control.is_focussable():
            for w in layout.find_all_windows():
                if w.content.is_focussable():
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

        call_from_executor(
            redraw, _max_postpone_until=_max_postpone_until)

    def _redraw(self, render_as_done=False):
        """
        Render the command line again. (Not thread safe!) (From other threads,
        or if unsure, use :meth:`.Application.invalidate`.)

        :param render_as_done: make sure to put the cursor after the UI.
        """
        # Only draw when no sub application was started.
        if self._is_running and not self._running_in_terminal:
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

            self.layout.update_parents_relations()

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

    def run_async(self, pre_run=None):
        """
        Run asynchronous. Return a `Future` object.
        """
        assert not self._is_running
        self._is_running = True
        previous_app = set_app(self)

        def _run_async():
            " Coroutine. "
            loop = get_event_loop()
            f = loop.create_future()
            self.future = f  # XXX: make sure to set this before calling '_redraw'.

            # Counter for cancelling 'flush' timeouts. Every time when a key is
            # pressed, we start a 'flush' timer for flushing our escape key. But
            # when any subsequent input is received, a new timer is started and
            # the current timer will be ignored.
            flush_counter = [0]  # Non local.

            # Reset.
            self.reset()
            self._pre_run(pre_run)

            # Feed type ahead input first.
            self.key_processor.feed_multiple(get_typeahead(self.input))
            self.key_processor.process_keys()

            def feed_keys(keys):
                self.key_processor.feed_multiple(keys)
                self.key_processor.process_keys()

            def read_from_input():
                # Ignore when we aren't running anymore. This callback will
                # removed from the loop next time. (It could be that it was
                # still in the 'tasks' list of the loop.)
                if not self._is_running:
                    return

                # Get keys from the input object.
                keys = self.input.read_keys()

                # Feed to key processor.
                self.key_processor.feed_multiple(keys)
                self.key_processor.process_keys()

                # Quit when the input stream was closed.
                if self.input.closed:
                    f.set_exception(EOFError)
                else:
                    # Increase this flush counter.
                    flush_counter[0] += 1
                    counter = flush_counter[0]

                    # Automatically flush keys.
                    # (_daemon needs to be set, otherwise, this will hang the
                    # application for .5 seconds before exiting.)
                    run_in_executor(
                        lambda: auto_flush_input(counter), _daemon=True)

            def auto_flush_input(counter):
                # Flush input after timeout.
                # (Used for flushing the enter key.)
                time.sleep(self.input_timeout)

                if flush_counter[0] == counter:
                    call_from_executor(flush_input)

            def flush_input():
                if not self.is_done:
                    # Get keys, and feed to key processor.
                    keys = self.input.flush_keys()
                    self.key_processor.feed_multiple(keys)
                    self.key_processor.process_keys()

                    if self.input.closed:
                        f.set_exception(EOFError)

            # Enter raw mode.
            with self.input.raw_mode():
                # Draw UI.
                self.renderer.request_absolute_cursor_position()
                self._redraw()

                # Set event loop handlers.
                previous_input, previous_cb = loop.set_input(self.input, read_from_input)

                has_sigwinch = hasattr(signal, 'SIGWINCH')
                if has_sigwinch:
                    previous_winch_handler = loop.add_signal_handler(
                        signal.SIGWINCH, self._on_resize)

                # Wait for UI to finish.
                try:
                    result = yield From(f)
                finally:
                    # In any case, when the application finishes. (Successful,
                    # or because of an error.)
                    try:
                        self._redraw(render_as_done=True)
                    finally:
                        # _redraw has a good chance to fail if it calls widgets
                        # with bad code. Make sure to reset the renderer anyway.
                        self.renderer.reset()

                        # Clear event loop handlers.
                        if previous_input:
                            loop.set_input(previous_input, previous_cb)
                        else:
                            loop.remove_input()

                        if has_sigwinch:
                            loop.add_signal_handler(signal.SIGWINCH, previous_winch_handler)

                        # Unset running Application.
                        self._is_running = False
                        set_app(previous_app)  # Make sure to do this after removing the input.

                        # Store unprocessed input as typeahead for next time.
                        store_typeahead(self.input, self.key_processor.flush())

                raise Return(result)

        def _run_async2():
            try:
                f = From(_run_async())
                result = yield f
            finally:
                assert not self._is_running
            raise Return(result)

        return ensure_future(_run_async2())

    def run(self, pre_run=None, set_exception_handler=True):
        """
        A blocking 'run' call that waits until the UI is finished.

        :param set_exception_handler: When set, in case of an exception, go out
            of the alternate screen and hide the application, display the
            exception, and wait for the user to press ENTER.
        """
        loop = get_event_loop()

        def run():
            f = self.run_async(pre_run=pre_run)
            run_until_complete(f)
            return f.result()

        def handle_exception(context):
            " Print the exception, using run_in_terminal. "
            def print_exception():
                loop.default_exception_handler(context)
                yield From(_do_wait_for_enter('Got an exception. Press ENTER to continue...'))
            self.run_coroutine_in_terminal(print_exception)

        if set_exception_handler:
            # Run with patched exception handler.
            previous_exc_handler = loop.get_exception_handler()
            loop.set_exception_handler(handle_exception)
            try:
                return run()
            finally:
                loop.set_exception_handler(previous_exc_handler)
        else:
            run()

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

    def run_in_terminal(self, func, render_cli_done=False, in_executor=False):
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
        :param in_executor: When True, run in executor. (Use this for long
            blocking functions, when you don't want to block the event loop.)

        :returns: A `Future`.
        """
        if in_executor:
            def async_func():
                f = run_in_executor(func)
                return f
        else:
            def async_func():
                result = func()
                return Future.succeed(result)

        return self.run_coroutine_in_terminal(async_func, render_cli_done=render_cli_done)

    def run_coroutine_in_terminal(self, async_func, render_cli_done=False):
        """
        `async_func` can be a coroutine or a function that returns a Future.

        :param async_func: A function that returns either a Future or coroutine
            when called.
        :returns: A `Future`.
        """
        assert callable(async_func)
        loop = get_event_loop()

        # When a previous `run_in_terminal` call was in progress. Wait for that
        # to finish, before starting this one. Chain to previous call.
        previous_run_in_terminal_f = self._running_in_terminal_f
        new_run_in_terminal_f = loop.create_future()
        self._running_in_terminal_f = new_run_in_terminal_f

        def _run_in_t():
            " Coroutine. "
            # Wait for the previous `run_in_terminal` to finish.
            yield previous_run_in_terminal_f

            # Draw interface in 'done' state, or erase.
            if render_cli_done:
                self._redraw(render_as_done=True)
            else:
                self.renderer.erase()

            # Disable rendering.
            self._running_in_terminal = True

            # Detach input.
            previous_input, previous_cb = loop.remove_input()
            try:
                with self.input.cooked_mode():
                    result = yield From(async_func())

                raise Return(result)  # Same as: "return result"
            finally:
                # Attach input again.
                loop.set_input(previous_input, previous_cb)

                # Redraw interface again.
                try:
                    self._running_in_terminal = False
                    self.renderer.reset()
                    self.renderer.request_absolute_cursor_position()
                    self._redraw()
                finally:
                    new_run_in_terminal_f.set_result(None)

        return ensure_future(_run_in_t())

    def run_system_command(self, command, wait_for_enter=True,
                           display_before_text='',
                           wait_text='Press ENTER to continue...'):
        """
        Run system command (While hiding the prompt. When finished, all the
        output will scroll above the prompt.)

        :param command: Shell command to be executed.
        :param wait_for_enter: FWait for the user to press enter, when the
            command is finished.
        :param display_before_text: If given, text to be displayed before the
            command executes.
        """
        assert isinstance(wait_for_enter, bool)

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
            def run_command():
                self.print_formatted_text(display_before_text)
                p = Popen(command, shell=True,
                          stdin=input_fd, stdout=output_fd)
                p.wait()
            yield run_in_executor(run_command)

            # Wait for the user to press enter.
            if wait_for_enter:
                yield From(_do_wait_for_enter(wait_text))

        self.run_coroutine_in_terminal(run)

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

    def print_formatted_text(self, formatted_text, style=None):
        """
        Print a list of (style_str, text) tuples to the output.
        (When the UI is running, this method has to be called through
        `run_in_terminal`, otherwise it will destroy the UI.)

        :param formatted_text: List of ``(style_str, text)`` tuples.
        :param style: Style class to use. Defaults to the active style in the CLI.
        """
        print_formatted_text(self.output, formatted_text, style or self.style)

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

    def _create_key_bindings(self, current_window, other_controls):
        """
        Create a `KeyBindings` object that merges the `KeyBindings` from the
        `UIControl` with all the parent controls and the global key bindings.
        """
        key_bindings = []

        # Collect key bindings from currently focussed control and all parent
        # controls. Don't include key bindings of container parent controls.
        container = current_window
        while container is not None:
            kb = container.get_key_bindings()
            if kb is not None:
                key_bindings.append(kb)

            if container.is_modal():
                break
            container = self.app.layout.get_parent(container)

        # Add App key bindings
        if self.app.key_bindings:
            key_bindings.append(self.app.key_bindings)

        # Add mouse bindings.
        key_bindings.append(ConditionalKeyBindings(
            self.app._page_navigation_bindings,
            self.app.enable_page_navigation_bindings))
        key_bindings.append(self.app._default_bindings)
        key_bindings.append(self.app._mouse_bindings)

        # Reverse this list. The current control's key bindings should come
        # last. They need priority.
        key_bindings = key_bindings[::-1]

        return merge_key_bindings(key_bindings)

    @property
    def _key_bindings(self):
        current_window = self.app.layout.current_window
        other_controls = list(self.app.layout.find_all_controls())
        key = current_window, frozenset(other_controls)

        return self._cache.get(
            key, lambda: self._create_key_bindings(current_window, other_controls))

    def get_bindings_for_keys(self, keys):
        return self._key_bindings.get_bindings_for_keys(keys)

    def get_bindings_starting_with_keys(self, keys):
        return self._key_bindings.get_bindings_starting_with_keys(keys)


def _do_wait_for_enter(wait_text):
    """
    Create a sub application to wait for the enter key press.
    This has two advantages over using 'input'/'raw_input':
    - This will share the same input/output I/O.
    - This doesn't block the event loop.
    """
    from prompt_toolkit.shortcuts import Prompt

    key_bindings = KeyBindings()

    @key_bindings.add('enter')
    def _(event):
        event.app.set_return_value(None)

    @key_bindings.add(Keys.Any)
    def _(event):
        " Disallow typing. "
        pass

    prompt = Prompt(
        message=wait_text,
        extra_key_bindings=key_bindings)
    yield prompt.app.run_async()
