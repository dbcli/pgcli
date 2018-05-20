"""
Formatter classes for the progress bar.
Each progress bar consists of a list of these formatters.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass, text_type
import time

from prompt_toolkit.formatted_text import HTML, to_formatted_text
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.utils import explode_text_fragments
from prompt_toolkit.formatted_text.utils import fragment_list_width

__all__ = [
    'Formatter',
    'Text',
    'Label',
    'Percentage',
    'Bar',
    'Progress',
    'TimeElapsed',
    'TimeLeft',
    'IterationsPerSecond',
    'SpinningWheel',
    'Rainbow',
    'create_default_formatters',
]


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


class Label(Formatter):
    """
    Display the name of the current task.

    :param width: If a `width` is given, use this width. Scroll the text if it
        doesn't fit in this width.
    :param suffix: String suffix to be added after the task name, e.g. ': '.
        If no task name was given, no suffix will be added.
    """
    def __init__(self, width=None, suffix=''):
        assert isinstance(suffix, text_type)
        self.width = width
        self.suffix = suffix

    def _add_suffix(self, label):
        label = to_formatted_text(label, style='class:label')
        return label + [('', self.suffix)]

    def format(self, progress_bar, progress, width):
        label = self._add_suffix(progress.label)
        cwidth = fragment_list_width(label)

        if cwidth > width:
            # It doesn't fit -> scroll task name.
            label = explode_text_fragments(label)
            max_scroll = cwidth - width
            current_scroll = int(time.time() * 3 % max_scroll)
            label = label[current_scroll:]

        return label

    def get_width(self, progress_bar):
        if self.width:
            return self.width

        all_labels = [self._add_suffix(c.label) for c in progress_bar.counters]
        if all_labels:
            max_widths = max(fragment_list_width(l) for l in all_labels)
            return D(preferred=max_widths, max=max_widths)
        else:
            return D()


class Percentage(Formatter):
    """
    Display the progress as a percentage.
    """
    template = '<percentage>{percentage:>5}%</percentage>'

    def format(self, progress_bar, progress, width):
        return HTML(self.template).format(
            percentage=round(progress.percentage, 1))

    def get_width(self, progress_bar):
        return D.exact(6)


class Bar(Formatter):
    """
    Display the progress bar itself.
    """
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
        width -= 3  # Subtract left '|', bar_b and right '|'

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
    """
    Display the progress as text.  E.g. "8/20"
    """
    template = '<current>{current:>3}</current>/<total>{total:>3}</total>'

    def format(self, progress_bar, progress, width):
        return HTML(self.template).format(
            current=progress.current,
            total=progress.total or '?')

    def get_width(self, progress_bar):
        all_lengths = [len('{0}'.format(c.total)) for c in progress_bar.counters]
        all_lengths.append(1)
        return D.exact(max(all_lengths) * 2 + 1)


def _format_timedelta(timedelta):
    """
    Return hh:mm:ss, or mm:ss if the amount of hours is zero.
    """
    result = '{0}'.format(timedelta).split('.')[0]
    if result.startswith('0:'):
        result = result[2:]
    return result


class TimeElapsed(Formatter):
    """
    Display the elapsed time.
    """
    def format(self, progress_bar, progress, width):
        text = _format_timedelta(progress.time_elapsed).rjust(width)
        return HTML('<time-elapsed>{time_elapsed}</time-elapsed>').format(time_elapsed=text)

    def get_width(self, progress_bar):
        all_values = [len(_format_timedelta(c.time_elapsed)) for c in progress_bar.counters]
        if all_values:
            return max(all_values)
        return 0


class TimeLeft(Formatter):
    """
    Display the time left.
    """
    template = '<time-left>{time_left}</time-left>'
    unknown = '?:??:??'

    def format(self, progress_bar, progress, width):
        if progress.total:
            time_left = _format_timedelta(progress.time_left)
        else:
            time_left = self.unknown

        return HTML(self.template).format(time_left=time_left.rjust(width))

    def get_width(self, progress_bar):
        all_values = [len(_format_timedelta(c.time_left)) if c.total else 7
                      for c in progress_bar.counters]
        if all_values:
            return max(all_values)
        return 0


class IterationsPerSecond(Formatter):
    """
    Display the iterations per second.
    """
    template = '<iterations-per-second>{iterations_per_second:.2f}</iterations-per-second>'

    def format(self, progress_bar, progress, width):
        value = progress.current / progress.time_elapsed.total_seconds()
        return HTML(self.template.format(iterations_per_second=value))

    def get_width(self, progress_bar):
        all_values = [len('{0:.2f}'.format(c.current / c.time_elapsed.total_seconds()))
                      for c in progress_bar.counters]
        if all_values:
            return max(all_values)
        return 0


class SpinningWheel(Formatter):
    """
    Display a spinning wheel.
    """
    characters = r'/-\|'

    def format(self, progress_bar, progress, width):
        index = int(time.time() * 3) % len(self.characters)
        return HTML('<spinning-wheel>{0}</spinning-wheel>').format(self.characters[index])

    def get_width(self, progress_bar):
        return D.exact(1)


def _hue_to_rgb(hue):
    " Take hue between 0 and 1, return (r, g, b). "
    i = int(hue * 6.)
    f = (hue * 6.) - i

    q = int(255 * (1. - f))
    t = int(255 * (1. - (1. - f)))

    i %= 6

    return [
        (255, t, 0),
        (q, 255, 0),
        (0, 255, t),
        (0, q, 255),
        (t, 0, 255),
        (255, 0, q),
    ][i]


class Rainbow(Formatter):
    """
    For the fun. Add rainbow colors to any of the other formatters.
    """
    colors = ['#%.2x%.2x%.2x' % _hue_to_rgb(h / 100.) for h in range(0, 100)]

    def __init__(self, formatter):
        self.formatter = formatter

    def format(self, progress_bar, progress, width):
        # Get formatted text from nested formatter, and explode it in
        # text/style tuples.
        result = self.formatter.format(progress_bar, progress, width)
        result = explode_text_fragments(to_formatted_text(result))

        # Insert colors.
        result2 = []
        shift = int(time.time() * 3) % len(self.colors)

        for i, (style, text) in enumerate(result):
            result2.append((style + ' ' + self.colors[(i + shift) % len(self.colors)], text))
        return result2

    def get_width(self, progress_bar):
        return self.formatter.get_width(progress_bar)


def create_default_formatters():
    """
    Return the list of default formatters.
    """
    return [
        Label(),
        Text(' '),
        Percentage(),
        Text(' '),
        Bar(),
        Text(' '),
        Progress(),
        Text(' '),
        Text('eta [', style='class:time-left'),
        TimeLeft(),
        Text(']', style='class:time-left'),
        Text(' '),
    ]
