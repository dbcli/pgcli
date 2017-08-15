"""
Progress bar implementation on top of prompt_toolkit.

::

    with progress_bar(...) as pb:
        for item in pb(data):
            ...
"""
from __future__ import unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.filters import Condition, is_done, renderer_height_is_known
from prompt_toolkit.formatted_text import to_formatted_text, HTML
from prompt_toolkit.input.vt100 import PipeInput
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, Window, ConditionalContainer, FormattedTextControl, HSplit
from prompt_toolkit.layout.controls import UIControl, UIContent
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.utils import in_main_thread
from prompt_toolkit.eventloop import get_event_loop

import datetime
import os
import signal
import threading

__all__ = (
    'progress_bar',
)


def default_format(progress_bar, progress, width):
    try:
        pb_width = width - 50 - len(progress.title)

        pb_a = int(progress.percentage * pb_width / 100)
        bar_a = '=' * pb_a
        bar_b = ' ' * (pb_width - pb_a)

        time_elapsed = progress.time_elapsed
        eta = progress.eta
        return HTML(
                '<b>{title}</b>'
                '{separator}'
                '{percentage:>5}%'
                ' |<completed abg="#888888">{bar_a}&gt;</completed><pending>{bar_b}</pending>| '
                '{current}/{total} '
                '{time_elapsed} eta <eta>[{eta}]</eta>'
                ).format(
            title=progress.title,
            separator=(': ' if progress.title else ''),
            percentage=round(progress.percentage, 1), 
            bar_a=bar_a,
            bar_b=bar_b,
            current=progress.current,
            total=progress.total,
            time_elapsed='{0}'.format(time_elapsed).split('.')[0],
            eta='{0}'.format(eta).split('.')[0],
            )
    except BaseException as e:
        import traceback; traceback.print_exc()
        return ''


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


class progress_bar(object):
    """
    Progress bar context manager.

    Usage ::

        with progress_bar(...) as pb:
            for item in pb(data):
                ...

    :param title: Text to be displayed above the progress bars. This can be a
        callable or formatted text as well.
    :param bottom_toolbar: Text to be displayed in the bottom toolbar.
        This can be a callable or formatted text.
    """
    def __init__(self, title=None, formatter=default_format, bottom_toolbar=None, style=None):
        self.title = title
        self.formatter = formatter
        self.bottom_toolbar = bottom_toolbar
        self.counters = []
        self.style = style
        self._thread = None

        self._loop = get_event_loop()
        self._previous_winch_handler = None
        self._has_sigwinch = False

    def __enter__(self):
        # Create UI Application.
        title_toolbar = ConditionalContainer(
            Window(FormattedTextControl(lambda: self.title), height=1),
            filter=Condition(lambda: self.title is not None))

        bottom_toolbar = ConditionalContainer(
            Window(FormattedTextControl(lambda: self.bottom_toolbar,
                                        style='class:bottom-toolbar.text'),
                   style='class:bottom-toolbar',
                   height=1),
            filter=~is_done & renderer_height_is_known &
                    Condition(lambda: self.bottom_toolbar is not None))

        self.app = Application(
            min_redraw_interval=.05,
            layout=Layout(HSplit([
                title_toolbar,
                Window(
                    content=_ProgressControl(self),
                    height=lambda: len(self.counters)),
                Window(),
                bottom_toolbar,
            ])),
            style=self.style)

        # Run application in different thread.
        def run():
            try:
                self.app.run()
            except Exception as e:
                import traceback; traceback.print_exc()
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
            self.app.set_return_value(None)

        # Remove WINCH handler.
        if self._has_sigwinch:
            self._loop.add_signal_handler(signal.SIGWINCH, self._previous_winch_handler)

        self._thread.join()

    def __call__(self, data=None, title='', remove_when_done=False, total=None):
        """
        Start a new counter.

        :param remove_when_done: When `True`, hide this progress bar.
        :param total: Specify the maximum value if it can't be calculated by
            calling ``len``.
        """
        counter = ProgressBarCounter(
            self, data, title=title, remove_when_done=remove_when_done, total=total)
        self.counters.append(counter)
        return counter

    def invalidate(self):
        self.app.invalidate()


class _ProgressControl(UIControl):
    """
    User control for the progress bar.
    """
    def __init__(self, progress_bar):
        self.progress_bar = progress_bar
        self._key_bindings = create_key_bindings()

    def create_content(self, width, height):
        items = []
        for pr in self.progress_bar.counters:
            items.append(to_formatted_text(
                self.progress_bar.formatter(self.progress_bar, pr, width)))

        def get_line(i):
            return items[i]
        return UIContent(
            get_line=get_line,
            line_count=len(items),
            show_cursor=False)

    def is_focussable(self):
        return True  # Make sure that the key bindings work.

    def get_key_bindings(self):
        return self._key_bindings


class ProgressBarCounter(object):
    """
    An individual counter (A progress bar can have multiple counters).
    """
    def __init__(self, progress_bar, data=None, title='', remove_when_done=False, total=None):
        self.start_time = datetime.datetime.now()
        self.progress_bar = progress_bar
        self.data = data
        self.current = 0
        self.title = title
        self.remove_when_done = remove_when_done
        self.done = False

        if total is None:
            self.total = len(data)
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
        return self.current * 100 / max(self.total, 1)

    @property
    def time_elapsed(self):
        """
        return how much time has been elapsed since the start.
        """
        return datetime.datetime.now() - self.start_time

    @property
    def eta(self):
        """
        Timedelta representing the ETA.
        """
        return self.time_elapsed / self.percentage * (100 - self.percentage)

