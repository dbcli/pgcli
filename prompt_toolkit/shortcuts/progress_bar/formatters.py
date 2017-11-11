"""
Formatter classes for the progress bar.
Each progress bar consists of a list of these formatters.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass
import time

from prompt_toolkit.formatted_text import HTML, to_formatted_text
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.utils import fragment_list_width
from prompt_toolkit.utils import get_cwidth

__all__ = (
    'Formatter',
    'Text',
    'TaskName',
    'Percentage',
    'Bar',
    'Progress',
    'ElapsedTime',
    'ETA',
)


class Formatter(with_metaclass(ABCMeta, object)):
    """
    Base class for any formatter.
    """
    @abstractmethod
    def format(self, progress_bar, progress, width):
        pass

    def get_width(self, progress_bar):
        return D()


class Text(Formatter):
    """
    Display plain text.
    """
    def __init__(self, text, style=''):
        self.text = to_formatted_text(text, style=style)

    def format(self, progress_bar, progress, width):
        return self.text

    def get_width(self, progress_bar):
        return fragment_list_width(self.text)


class TaskName(Formatter):
    """
    Display the name of the current task.

    If `width` is given, use this width. Scroll the text if it doesn't fit in
    this width.
    """
    template = '<taskname>{name}</taskname>'

    def __init__(self, width=None):
        self.width = width

    def format(self, progress_bar, progress, width):
        task_name = progress.task_name
        cwidth = get_cwidth(task_name)

        if cwidth > width:
            # It doesn't fit -> scroll task name.
            max_scroll = cwidth - width
            current_scroll = int(time.time() * 3 % max_scroll)
            task_name = task_name[current_scroll:]

        # It does fit.
        return HTML(self.template).format(name=task_name)

    def get_width(self, progress_bar):
        if self.width:
            return self.width

        all_names = [c.task_name for c in progress_bar.counters]
        if all_names:
            max_widths = max(get_cwidth(name) for name in all_names)
            return D(preferred=max_widths, max=max_widths)
        else:
            return D()


class Percentage(Formatter):
    template = '<percentage>{percentage:>5}%</percentage>'

    def format(self, progress_bar, progress, width):
        return HTML(self.template).format(
            percentage=round(progress.percentage, 1))

    def get_width(self, progress_bar):
        return D.exact(6)


class Bar(Formatter):
    template = '<bar>{start}<bar-a>{bar_a}</bar-a><bar-b>{bar_b}</bar-b><bar-c>{bar_c}</bar-c>{end}</bar>'

    def __init__(self, start='[', end=']', sym_a='=', sym_b='>', sym_c=' ', unknown='#'):
        assert len(sym_a) == 1
        assert len(sym_b) == 1
        assert len(sym_c) == 1

        self.start = start
        self.end = end
        self.sym_a = sym_a
        self.sym_b = sym_b
        self.sym_c = sym_c
        self.unknown = unknown

    def format(self, progress_bar, progress, width):
        width -= 3  # Substract left '|', bar_b and right '|'

        if progress.total:
            pb_a = int(progress.percentage * width / 100)
            bar_a = self.sym_a * pb_a
            bar_b = self.sym_b
            bar_c = self.sym_c * (width - pb_a)
        else:
            # Total is unknown.
            pb_a = int(time.time() * 20  % 100 * width / 100)
            bar_a = self.sym_c * pb_a
            bar_b = self.unknown
            bar_c = self.sym_c * (width - pb_a)

        return HTML(self.template).format(
            start=self.start,
            end=self.end,
            bar_a=bar_a,
            bar_b=bar_b,
            bar_c=bar_c)

    def get_width(self, progress_bar):
        return D(min=9)


class Progress(Formatter):
    template = '<current>{current:>3}</current>/<total>{total:>3}</total>'

    def format(self, progress_bar, progress, width):
        return HTML(self.template).format(
            current=progress.current,
            total=progress.total or '?')

    def get_width(self, progress_bar):
        all_lengths = [len('{0}'.format(c.total)) for c in progress_bar.counters]
        all_lengths.append(1)
        return D.exact(max(all_lengths) * 2 + 1)


class ElapsedTime(Formatter):
    def format(self, progress_bar, progress, width):
        return HTML('<time-elapsed>{time_elapsed}</time-elapsed>').format(
            time_elapsed=progress.time_elapsed)

    def get_width(self, progress_bar):
        return D.exact(8)


class ETA(Formatter):
    template = '<eta>eta [<value>{eta}</value>]</eta>'
    unknown = '?:??:??'

    def format(self, progress_bar, progress, width):
        if progress.total:
            eta = '{0}'.format(progress.eta).split('.')[0]
        else:
            eta = self.unknown

        return HTML(self.template).format(eta=eta)

    def get_width(self, progress_bar):
        text = to_formatted_text(HTML(self.template).format(eta=self.unknown))
        return fragment_list_width(text)


class SpinningWheel(Formatter):
    characters = r'/-\|'

    def format(self, progress_bar, progress, width):
        index = int(time.time() * 3) % len(self.characters)
        return HTML('<spinning-wheel>{0}</spinning-wheel>').format(self.characters[index])

    def get_width(self, progress_bar):
        return D.exact(1)
