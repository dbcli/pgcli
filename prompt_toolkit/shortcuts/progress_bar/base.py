"""
Progress bar implementation on top of prompt_toolkit.

::

    with ProgressBar(...) as pb:
        for item in pb(data):
            ...
"""
from __future__ import unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.eventloop import get_event_loop
from prompt_toolkit.filters import Condition, is_done, renderer_height_is_known
from prompt_toolkit.formatted_text import to_formatted_text, is_formatted_text
from prompt_toolkit.input.defaults import get_default_input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, Window, ConditionalContainer, FormattedTextControl, HSplit, VSplit
from prompt_toolkit.layout.controls import UIControl, UIContent
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.utils import in_main_thread

import functools
import contextlib
import datetime
import os
import signal
import threading
import time
import traceback
import sys

from .formatters import create_default_formatters, Formatter

__all__ = [
    'ProgressBar',
]


def create_key_bindings():
    """
    Key bindings handled by the progress bar.
    (The main thread is not supposed to handle any key bindings.)
    """
    kb = KeyBindings()

    @kb.add('c-l')
    def _(event):
        event.app.renderer.clear()

    @kb.add('c-c')
    def _(event):
        # Send KeyboardInterrupt to the main thread.
        os.kill(os.getpid(), signal.SIGINT)

    return kb


class ProgressBar(object):
    """
    Progress bar context manager.

    Usage ::

        with ProgressBar(...) as pb:
            for item in pb(data):
                ...

    :param title: Text to be displayed above the progress bars. This can be a
        callable or formatted text as well.
    :param formatters: List of :class:`.Formatter` instances.
    :param bottom_toolbar: Text to be displayed in the bottom toolbar. This
        can be a callable or formatted text.
    :param style: :class:`prompt_toolkit.styles.BaseStyle` instance.
    :param key_bindings: :class:`.KeyBindings` instance.
    :param file: The file object used for rendering, by default `sys.stderr` is used.

    :param color_depth: `prompt_toolkit` `ColorDepth` instance.
    :param output: :class:`~prompt_toolkit.output.Output` instance.
    :param input: :class:`~prompt_toolkit.input.Input` instance.
    """
    def __init__(self, title=None, formatters=None, bottom_toolbar=None,
                 style=None, key_bindings=None, file=None, color_depth=None,
                 output=None, input=None):
        assert formatters is None or (
            isinstance(formatters, list) and all(isinstance(fo, Formatter) for fo in formatters))
        assert style is None or isinstance(style, BaseStyle)
        assert key_bindings is None or isinstance(key_bindings, KeyBindings)

        self.title = title
        self.formatters = formatters or create_default_formatters()
        self.bottom_toolbar = bottom_toolbar
        self.counters = []
        self.style = style
        self.key_bindings = key_bindings

        # Note that we use __stderr__ as default error output, because that
        # works best with `patch_stdout`.
        self.color_depth = color_depth
        self.output = output or create_output(stdout=file or sys.__stderr__)
        self.input = input or get_default_input()

        self._thread = None

        self._loop = get_event_loop()
        self._previous_winch_handler = None
        self._has_sigwinch = False

    def __enter__(self):
        # Create UI Application.
        title_toolbar = ConditionalContainer(
            Window(FormattedTextControl(lambda: self.title), height=1, style='class:progressbar,title'),
            filter=Condition(lambda: self.title is not None))

        bottom_toolbar = ConditionalContainer(
            Window(FormattedTextControl(lambda: self.bottom_toolbar,
                                        style='class:bottom-toolbar.text'),
                   style='class:bottom-toolbar',
                   height=1),
            filter=~is_done & renderer_height_is_known &
                Condition(lambda: self.bottom_toolbar is not None))

        def width_for_formatter(formatter):
            # Needs to be passed as callable (partial) to the 'width'
            # parameter, because we want to call it on every resize.
            return formatter.get_width(progress_bar=self)

        progress_controls = [
            Window(
                content=_ProgressControl(self, f),
                width=functools.partial(width_for_formatter, f))
            for f in self.formatters
        ]

        self.app = Application(
            min_redraw_interval=.05,
            layout=Layout(HSplit([
                title_toolbar,
                VSplit(progress_controls,
                       height=lambda: D(
                           preferred=len(self.counters),
                           max=len(self.counters))),
                Window(),
                bottom_toolbar,
            ])),
            style=self.style,
            key_bindings=self.key_bindings,
            color_depth=self.color_depth,
            output=self.output,
            input=self.input)

        # Run application in different thread.
        def run():
            with _auto_refresh_context(self.app, .3):
                try:
                    self.app.run()
                except BaseException as e:
                    traceback.print_exc()
                    print(e)

        self._thread = threading.Thread(target=run)
        self._thread.start()

        # Attach WINCH signal handler in main thread.
        # (Interrupt that we receive during resize events.)
        self._has_sigwinch = hasattr(signal, 'SIGWINCH') and in_main_thread()
        if self._has_sigwinch:
            self._previous_winch_handler = self._loop.add_signal_handler(
                signal.SIGWINCH, self.app.invalidate)

        return self

    def __exit__(self, *a):
        # Quit UI application.
        if self.app.is_running:
            self.app.exit()

        # Remove WINCH handler.
        if self._has_sigwinch:
            self._loop.add_signal_handler(signal.SIGWINCH, self._previous_winch_handler)

        self._thread.join()

    def __call__(self, data=None, label='', remove_when_done=False, total=None):
        """
        Start a new counter.

        :param label: Title text or description for this progress. (This can be
            formatted text as well).
        :param remove_when_done: When `True`, hide this progress bar.
        :param total: Specify the maximum value if it can't be calculated by
            calling ``len``.
        """
        assert is_formatted_text(label)
        assert isinstance(remove_when_done, bool)

        counter = ProgressBarCounter(
            self, data, label=label, remove_when_done=remove_when_done, total=total)
        self.counters.append(counter)
        return counter

    def invalidate(self):
        self.app.invalidate()


class _ProgressControl(UIControl):
    """
    User control for the progress bar.
    """
    def __init__(self, progress_bar, formatter):
        self.progress_bar = progress_bar
        self.formatter = formatter
        self._key_bindings = create_key_bindings()

    def create_content(self, width, height):
        items = []
        for pr in self.progress_bar.counters:
            try:
                text = self.formatter.format(self.progress_bar, pr, width)
            except BaseException:
                traceback.print_exc()
                text = 'ERROR'

            items.append(to_formatted_text(text))

        def get_line(i):
            return items[i]

        return UIContent(
            get_line=get_line,
            line_count=len(items),
            show_cursor=False)

    def is_focusable(self):
        return True  # Make sure that the key bindings work.

    def get_key_bindings(self):
        return self._key_bindings


class ProgressBarCounter(object):
    """
    An individual counter (A progress bar can have multiple counters).
    """
    def __init__(self, progress_bar, data=None, label='', remove_when_done=False, total=None):
        self.start_time = datetime.datetime.now()
        self.progress_bar = progress_bar
        self.data = data
        self.current = 0
        self.label = label
        self.remove_when_done = remove_when_done
        self.done = False

        if total is None:
            try:
                self.total = len(data)
            except TypeError:
                self.total = None  # We don't know the total length.
        else:
            self.total = total

    def __iter__(self):
        try:
            for item in self.data:
                self.current += 1
                self.progress_bar.invalidate()
                yield item
        finally:
            self.done = True

            if self.remove_when_done:
                self.progress_bar.counters.remove(self)

    @property
    def percentage(self):
        if self.total is None:
            return 0
        else:
            return self.current * 100 / max(self.total, 1)

    @property
    def time_elapsed(self):
        """
        return how much time has been elapsed since the start.
        """
        return datetime.datetime.now() - self.start_time

    @property
    def time_left(self):
        """
        Timedelta representing the time left.
        """
        if self.total is None or not self.percentage:
            return None
        else:
            return self.time_elapsed * (100 - self.percentage) / self.percentage


@contextlib.contextmanager
def _auto_refresh_context(app, refresh_interval=None):
    " Return a context manager for the auto-refresh loop. "
    done = [False]  # nonlocal

    # Enter.

    def run():
        while not done[0]:
            time.sleep(refresh_interval)
            app.invalidate()

    if refresh_interval:
        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

    try:
        yield
    finally:
        # Exit.
        done[0] = True
