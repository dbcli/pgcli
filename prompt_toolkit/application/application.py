from __future__ import unicode_literals

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.cache import SimpleCache
from prompt_toolkit.clipboard import Clipboard, InMemoryClipboard
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.eventloop import get_event_loop, ensure_future, Return, run_in_executor, run_until_complete, call_from_executor, From
from prompt_toolkit.eventloop.base import get_traceback_from_context
from prompt_toolkit.filters import to_filter, Condition
from prompt_toolkit.input.base import Input
from prompt_toolkit.input.defaults import get_default_input
from prompt_toolkit.input.typeahead import store_typeahead, get_typeahead
from prompt_toolkit.key_binding.bindings.page_navigation import load_page_navigation_bindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, ConditionalKeyBindings, KeyBindingsBase, merge_key_bindings, GlobalOnlyKeyBindings
from prompt_toolkit.key_binding.key_processor import KeyProcessor
from prompt_toolkit.key_binding.emacs_state import EmacsState
from prompt_toolkit.key_binding.vi_state import ViState
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.dummy import create_dummy_layout
from prompt_toolkit.layout.layout import Layout, walk
from prompt_toolkit.output import Output, ColorDepth
from prompt_toolkit.output.defaults import get_default_output
from prompt_toolkit.renderer import Renderer, print_formatted_text
from prompt_toolkit.search import SearchState
from prompt_toolkit.styles import BaseStyle, default_ui_style, default_pygments_style, merge_styles, DynamicStyle, DummyStyle
from prompt_toolkit.utils import Event, in_main_thread
from .current import set_app
from .run_in_terminal import run_in_terminal, run_coroutine_in_terminal

from subprocess import Popen
from traceback import format_tb
import os
import re
import signal
import six
import sys
import time

__all__ = [
    'Application',
]


class Application(object):
    """
    The main Application class!
    This glues everything together.

    :param layout: A :class:`~prompt_toolkit.layout.Layout` instance.
    :param key_bindings:
        :class:`~prompt_toolkit.key_binding.KeyBindingsBase` instance for
        the key bindings.
    :param clipboard: :class:`~prompt_toolkit.clipboard.Clipboard` to use.
    :param on_abort: What to do when Control-C is pressed.
    :param on_exit: What to do when Control-D is pressed.
    :param full_screen: When True, run the application on the alternate screen buffer.
    :param color_depth: Any :class:`~.ColorDepth` value, a callable that
        returns a :class:`~.ColorDepth` or `None` for default.
    :param erase_when_done: (bool) Clear the application output when it finishes.
    :param reverse_vi_search_direction: Normally, in Vi mode, a '/' searches
        forward and a '?' searches backward. In Readline mode, this is usually
        reversed.
    :param min_redraw_interval: Number of seconds to wait between redraws. Use
        this for applications where `invalidate` is called a lot. This could cause
        a lot of terminal output, which some terminals are not able to process.

        `None` means that every `invalidate` will be scheduled right away
        (which is usually fine).

        When one `invalidate` is called, but a scheduled redraw of a previous
        `invalidate` call has not been executed yet, nothing will happen in any
        case.

    :param max_render_postpone_time: When there is high CPU (a lot of other
        scheduled calls), postpone the rendering max x seconds.  '0' means:
        don't postpone. '.5' means: try to draw at least twice a second.

    Filters:

    :param mouse_support: (:class:`~prompt_toolkit.filters.Filter` or
        boolean). When True, enable mouse support.
    :param paste_mode: :class:`~prompt_toolkit.filters.Filter` or boolean.
    :param editing_mode: :class:`~prompt_toolkit.enums.EditingMode`.

    :param enable_page_navigation_bindings: When `True`, enable the page
        navigation key bindings. These include both Emacs and Vi bindings like
        page-up, page-down and so on to scroll through pages. Mostly useful for
        creating an editor or other full screen applications. Probably, you
        don't want this for the implementation of a REPL. By default, this is
        enabled if `full_screen` is set.

    Callbacks (all of these should accept a
    :class:`~prompt_toolkit.application.Application` object as input.)

    :param on_reset: Called during reset.
    :param on_invalidate: Called when the UI has been invalidated.
    :param before_render: Called right before rendering.
    :param after_render: Called right after rendering.

    I/O:

    :param input: :class:`~prompt_toolkit.input.Input` instance.
    :param output: :class:`~prompt_toolkit.output.Output` instance. (Probably
                   Vt100_Output or Win32Output.)

    Usage:

        app = Application(...)
        app.run()
    """
    def __init__(self, layout=None,
                 style=None, include_default_pygments_style=True,
                 key_bindings=None, clipboard=None,
                 full_screen=False, color_depth=None,
                 mouse_support=False,

                 enable_page_navigation_bindings=None,  # Can be None, True or False.

                 paste_mode=False,
                 editing_mode=EditingMode.EMACS,
                 erase_when_done=False,
                 reverse_vi_search_direction=False,
                 min_redraw_interval=None,
                 max_render_postpone_time=0,

                 on_reset=None, on_invalidate=None,
                 before_render=None, after_render=None,

                 # I/O.
                 input=None, output=None):

        # If `enable_page_navigation_bindings` is not specified, enable it in
        # case of full screen applications only. This can be overridden by the user.
        if enable_page_navigation_bindings is None:
            enable_page_navigation_bindings = Condition(lambda: self.full_screen)

        paste_mode = to_filter(paste_mode)
        mouse_support = to_filter(mouse_support)
        reverse_vi_search_direction = to_filter(reverse_vi_search_direction)
        enable_page_navigation_bindings = to_filter(enable_page_navigation_bindings)
        include_default_pygments_style = to_filter(include_default_pygments_style)

        assert layout is None or isinstance(layout, Layout), 'Got layout: %r' % (layout, )
        assert key_bindings is None or isinstance(key_bindings, KeyBindingsBase)
        assert clipboard is None or isinstance(clipboard, Clipboard)
        assert isinstance(full_screen, bool)
        assert (color_depth is None or callable(color_depth) or
                color_depth in ColorDepth._ALL), 'Got color_depth: %r' % (color_depth, )
        assert isinstance(editing_mode, six.string_types)
        assert style is None or isinstance(style, BaseStyle)
        assert isinstance(erase_when_done, bool)
        assert min_redraw_interval is None or isinstance(min_redraw_interval, (float, int))
        assert max_render_postpone_time is None or isinstance(max_render_postpone_time, (float, int))

        assert on_reset is None or callable(on_reset)
        assert on_invalidate is None or callable(on_invalidate)
        assert before_render is None or callable(before_render)
        assert after_render is None or callable(after_render)

        assert output is None or isinstance(output, Output)
        assert input is None or isinstance(input, Input)

        self.style = style

        if layout is None:
            layout = create_dummy_layout()

        # Key bindings.
        self.key_bindings = key_bindings
        self._default_bindings = load_key_bindings()
        self._page_navigation_bindings = load_page_navigation_bindings()

        self.layout = layout
        self.clipboard = clipboard or InMemoryClipboard()
        self.full_screen = full_screen
        self._color_depth = color_depth
        self.mouse_support = mouse_support

        self.paste_mode = paste_mode
        self.editing_mode = editing_mode
        self.erase_when_done = erase_when_done
        self.reverse_vi_search_direction = reverse_vi_search_direction
        self.enable_page_navigation_bindings = enable_page_navigation_bindings
        self.min_redraw_interval = min_redraw_interval
        self.max_render_postpone_time = max_render_postpone_time

        # Events.
        self.on_invalidate = Event(self, on_invalidate)
        self.on_reset = Event(self, on_reset)
        self.before_render = Event(self, before_render)
        self.after_render = Event(self, after_render)

        # I/O.
        self.output = output or get_default_output()
        self.input = input or get_default_input()

        # List of 'extra' functions to execute before a Application.run.
        self.pre_run_callables = []

        self._is_running = False
        self.future = None

        #: Quoted insert. This flag is set if we go into quoted insert mode.
        self.quoted_insert = False

        #: Vi state. (For Vi key bindings.)
        self.vi_state = ViState()
        self.emacs_state = EmacsState()

        #: When to flush the input (For flushing escape keys.) This is important
        #: on terminals that use vt100 input. We can't distinguish the escape
        #: key from for instance the left-arrow key, if we don't know what follows
        #: after "\x1b". This little timer will consider "\x1b" to be escape if
        #: nothing did follow in this time span.
        #: This seems to work like the `ttimeoutlen` option in Vim.
        self.ttimeoutlen = .5  # Seconds.

        #: Like Vim's `timeoutlen` option. This can be `None` or a float.  For
        #: instance, suppose that we have a key binding AB and a second key
        #: binding A. If the uses presses A and then waits, we don't handle
        #: this binding yet (unless it was marked 'eager'), because we don't
        #: know what will follow. This timeout is the maximum amount of time
        #: that we wait until we call the handlers anyway. Pass `None` to
        #: disable this timeout.
        self.timeoutlen = 1.0

        #: The `Renderer` instance.
        # Make sure that the same stdout is used, when a custom renderer has been passed.
        self._merged_style = self._create_merged_style(include_default_pygments_style)

        self.renderer = Renderer(
            self._merged_style,
            self.output,
            full_screen=full_screen,
            mouse_support=mouse_support,
            cpr_not_supported_callback=self.cpr_not_supported_callback)

        #: Render counter. This one is increased every time the UI is rendered.
        #: It can be used as a key for caching certain information during one
        #: rendering.
        self.render_counter = 0

        # Invalidate flag. When 'True', a repaint has been scheduled.
        self._invalidated = False
        self._invalidate_events = []  # Collection of 'invalidate' Event objects.
        self._last_redraw_time = 0  # Unix timestamp of last redraw. Used when
                                    # `min_redraw_interval` is given.

        #: The `InputProcessor` instance.
        self.key_processor = KeyProcessor(_CombinedRegistry(self))

        # If `run_in_terminal` was called. This will point to a `Future` what will be
        # set at the point when the previous run finishes.
        self._running_in_terminal = False
        self._running_in_terminal_f = None

        # Trigger initialize callback.
        self.reset()

    def _create_merged_style(self, include_default_pygments_style):
        """
        Create a `Style` object that merges the default UI style, the default
        pygments style, and the custom user style.
        """
        dummy_style = DummyStyle()
        pygments_style = default_pygments_style()

        @DynamicStyle
        def conditional_pygments_style():
            if include_default_pygments_style():
                return pygments_style
            else:
                return dummy_style

        return merge_styles([
            default_ui_style(),
            conditional_pygments_style,
            DynamicStyle(lambda: self.style),
        ])

    @property
    def color_depth(self):
        """
        Active :class:`.ColorDepth`.
        """
        depth = self._color_depth

        if callable(depth):
            depth = depth()

        if depth is None:
            depth = ColorDepth.default()

        return depth

    @property
    def current_buffer(self):
        """
        The currently focused :class:`~.Buffer`.

        (This returns a dummy :class:`.Buffer` when none of the actual buffers
        has the focus. In this case, it's really not practical to check for
        `None` values or catch exceptions every time.)
        """
        return self.layout.current_buffer or Buffer(name='dummy-buffer')  # Dummy buffer.

    @property
    def current_search_state(self):
        """
        Return the current :class:`.SearchState`. (The one for the focused
        :class:`.BufferControl`.)
        """
        ui_control = self.layout.current_control
        if isinstance(ui_control, BufferControl):
            return ui_control.search_state
        else:
            return SearchState()  # Dummy search state.  (Don't return None!)

    def reset(self):
        """
        Reset everything, for reading the next input.
        """
        # Notice that we don't reset the buffers. (This happens just before
        # returning, and when we have multiple buffers, we clearly want the
        # content in the other buffers to remain unchanged between several
        # calls of `run`. (And the same is true for the focus stack.)

        self.exit_style = ''

        self.renderer.reset()
        self.key_processor.reset()
        self.layout.reset()
        self.vi_state.reset()
        self.emacs_state.reset()

        # Trigger reset event.
        self.on_reset.fire()

        # Make sure that we have a 'focusable' widget focused.
        # (The `Layout` class can't determine this.)
        layout = self.layout

        if not layout.current_control.is_focusable():
            for w in layout.find_all_windows():
                if w.content.is_focusable():
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

        def schedule_redraw():
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

        if self.min_redraw_interval:
            # When a minimum redraw interval is set, wait minimum this amount
            # of time between redraws.
            diff = time.time() - self._last_redraw_time
            if diff < self.min_redraw_interval:
                def redraw_in_future():
                    time.sleep(self.min_redraw_interval - diff)
                    schedule_redraw()
                run_in_executor(redraw_in_future)
            else:
                schedule_redraw()
        else:
            schedule_redraw()

    @property
    def invalidated(self):
        " True when a redraw operation has been scheduled. "
        return self._invalidated

    def _redraw(self, render_as_done=False):
        """
        Render the command line again. (Not thread safe!) (From other threads,
        or if unsure, use :meth:`.Application.invalidate`.)

        :param render_as_done: make sure to put the cursor after the UI.
        """
        # Only draw when no sub application was started.
        if self._is_running and not self._running_in_terminal:
            if self.min_redraw_interval:
                self._last_redraw_time = time.time()

            # Clear the 'rendered_ui_controls' list. (The `Window` class will
            # populate this during the next rendering.)
            self.rendered_user_controls = []

            # Render
            self.render_counter += 1
            self.before_render.fire()

            # NOTE: We want to make sure this Application is the active one, if
            #       we have a situation with multiple concurrent running apps.
            #       We had the case with pymux where `invalidate()` was called
            #       at the point where another Application was active. This
            #       would cause prompt_toolkit to render the wrong application
            #       to this output device.
            with set_app(self):
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
            self.after_render.fire()

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
        # (All controls are able to invalidate themselves.)
        def gather_events():
            for c in self.layout.find_all_controls():
                for ev in c.get_invalidate_events():
                    yield ev

        self._invalidate_events = list(gather_events())

        # Attach invalidate event handler.
        def invalidate(sender):
            self.invalidate()

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
        self.renderer.erase(leave_alternate_screen=False)
        self._request_absolute_cursor_position()
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
        Run asynchronous. Return a prompt_toolkit
        :class:`~prompt_toolkit.eventloop.Future` object.

        If you wish to run on top of asyncio, remember that a prompt_toolkit
        `Future` needs to be converted to an asyncio `Future`. The cleanest way
        is to call :meth:`~prompt_toolkit.eventloop.Future.to_asyncio_future`.
        Also make sure to tell prompt_toolkit to use the asyncio event loop.

        .. code:: python

            from prompt_toolkit.eventloop import use_asyncio_event_loop
            from asyncio import get_event_loop

            use_asyncio_event_loop()
            get_event_loop().run_until_complete(
                application.run_async().to_asyncio_future())

        """
        assert not self._is_running

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

            def read_from_input():
                # Ignore when we aren't running anymore. This callback will
                # removed from the loop next time. (It could be that it was
                # still in the 'tasks' list of the loop.)
                # Except: if we need to process incoming CPRs.
                if not self._is_running and not self.renderer.waiting_for_cpr:
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
                time.sleep(self.ttimeoutlen)

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
                with self.input.attach(read_from_input):
                    # Draw UI.
                    self._request_absolute_cursor_position()
                    self._redraw()

                    has_sigwinch = hasattr(signal, 'SIGWINCH') and in_main_thread()
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

                            # Unset `is_running`, this ensures that possibly
                            # scheduled draws won't paint during the following
                            # yield.
                            self._is_running = False

                            # Wait for CPR responses.
                            if self.input.responds_to_cpr:
                                yield From(self.renderer.wait_for_cpr_responses())

                            if has_sigwinch:
                                loop.add_signal_handler(signal.SIGWINCH, previous_winch_handler)

                            # Wait for the run-in-terminals to terminate.
                            previous_run_in_terminal_f = self._running_in_terminal_f

                            if previous_run_in_terminal_f:
                                yield From(previous_run_in_terminal_f)

                            # Store unprocessed input as typeahead for next time.
                            store_typeahead(self.input, self.key_processor.empty_queue())

                raise Return(result)

        def _run_async2():
            self._is_running = True
            with set_app(self):
                try:
                    f = From(_run_async())
                    result = yield f
                finally:
                    assert not self._is_running
                raise Return(result)

        return ensure_future(_run_async2())

    def run(self, pre_run=None, set_exception_handler=True, inputhook=None):
        """
        A blocking 'run' call that waits until the UI is finished.

        :param set_exception_handler: When set, in case of an exception, go out
            of the alternate screen and hide the application, display the
            exception, and wait for the user to press ENTER.
        :param inputhook: None or a callable that takes an `InputHookContext`.
        """
        loop = get_event_loop()

        def run():
            f = self.run_async(pre_run=pre_run)
            run_until_complete(f, inputhook=inputhook)
            return f.result()

        def handle_exception(context):
            " Print the exception, using run_in_terminal. "
            # For Python 2: we have to get traceback at this point, because
            # we're still in the 'except:' block of the event loop where the
            # traceback is still available. Moving this code in the
            # 'print_exception' coroutine will loose the exception.
            tb = get_traceback_from_context(context)
            formatted_tb = ''.join(format_tb(tb))

            def print_exception():
                # Print output. Similar to 'loop.default_exception_handler',
                # but don't use logger. (This works better on Python 2.)
                print('\nUnhandled exception in event loop:')
                print(formatted_tb)
                print('Exception %s' % (context.get('exception'), ))

                yield From(_do_wait_for_enter('Press ENTER to continue...'))
            run_coroutine_in_terminal(print_exception)

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

    def cpr_not_supported_callback(self):
        """
        Called when we don't receive the cursor position response in time.
        """
        if not self.input.responds_to_cpr:
            return  # We know about this already.

        def in_terminal():
            self.output.write(
                "WARNING: your terminal doesn't support cursor position requests (CPR).\r\n")
            self.output.flush()
        run_in_terminal(in_terminal)

    def exit(self, result=None, exception=None, style=''):
        """
        Exit application.

        :param result: Set this result for the application.
        :param exception: Set this exception as the result for an application. For
            a prompt, this is often `EOFError` or `KeyboardInterrupt`.
        :param style: Apply this style on the whole content when quitting,
            often this is 'class:exiting' for a prompt. (Used when
            `erase_when_done` is not set.)
        """
        assert result is None or exception is None

        if self.future.done():
            raise Exception('Return value already set.')

        self.exit_style = style

        if exception is not None:
            self.future.set_exception(exception)
        else:
            self.future.set_result(result)

    def _request_absolute_cursor_position(self):
        """
        Send CPR request.
        """
        # Note: only do this if the input queue is not empty, and a return
        # value has not been set. Otherwise, we won't be able to read the
        # response anyway.
        if not self.key_processor.input_queue and not self.is_done:
            self.renderer.request_absolute_cursor_position()

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
        :return: A `Future` object.
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
                self.print_text(display_before_text)
                p = Popen(command, shell=True,
                          stdin=input_fd, stdout=output_fd)
                p.wait()
            yield run_in_executor(run_command)

            # Wait for the user to press enter.
            if wait_for_enter:
                yield From(_do_wait_for_enter(wait_text))

        return run_coroutine_in_terminal(run)

    def suspend_to_background(self, suspend_group=True):
        """
        (Not thread safe -- to be called from inside the key bindings.)
        Suspend process.

        :param suspend_group: When true, suspend the whole process group.
            (This is the default, and probably what you want.)
        """
        # Only suspend when the operating system supports it.
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

            run_in_terminal(run)

    def print_text(self, text, style=None):
        """
        Print a list of (style_str, text) tuples to the output.
        (When the UI is running, this method has to be called through
        `run_in_terminal`, otherwise it will destroy the UI.)

        :param text: List of ``(style_str, text)`` tuples.
        :param style: Style class to use. Defaults to the active style in the CLI.
        """
        print_formatted_text(self.output, text, style or self._merged_style, self.color_depth)

    @property
    def is_running(self):
        " `True` when the application is currently active/running. "
        return self._is_running

    @property
    def is_done(self):
        return self.future and self.future.done()

    def get_used_style_strings(self):
        """
        Return a list of used style strings. This is helpful for debugging, and
        for writing a new `Style`.
        """
        return sorted([
            re.sub(r'\s+', ' ', style_str).strip()
            for style_str in self.renderer._attrs_for_style.keys()])


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
        collected_containers = set()

        # Collect key bindings from currently focused control and all parent
        # controls. Don't include key bindings of container parent controls.
        container = current_window
        while True:
            collected_containers.add(container)
            kb = container.get_key_bindings()
            if kb is not None:
                key_bindings.append(kb)

            if container.is_modal():
                break

            parent = self.app.layout.get_parent(container)
            if parent is None:
                break
            else:
                container = parent

        # Include global bindings (starting at the top-model container).
        for c in walk(container):
            if c not in collected_containers:
                kb = c.get_key_bindings()
                if kb is not None:
                    key_bindings.append(GlobalOnlyKeyBindings(kb))

        # Add App key bindings
        if self.app.key_bindings:
            key_bindings.append(self.app.key_bindings)

        # Add mouse bindings.
        key_bindings.append(ConditionalKeyBindings(
            self.app._page_navigation_bindings,
            self.app.enable_page_navigation_bindings))
        key_bindings.append(self.app._default_bindings)

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
    from prompt_toolkit.shortcuts import PromptSession

    key_bindings = KeyBindings()

    @key_bindings.add('enter')
    def _(event):
        event.app.exit()

    @key_bindings.add(Keys.Any)
    def _(event):
        " Disallow typing. "
        pass

    session = PromptSession(
        message=wait_text,
        key_bindings=key_bindings)
    yield From(session.app.run_async())
