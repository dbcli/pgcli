"""
"""
from __future__ import unicode_literals
from prompt_toolkit.eventloop import generator_to_async_generator, AsyncGeneratorItem
from abc import ABCMeta, abstractmethod
from six import with_metaclass, text_type

__all__ = [
    'Completion',
    'Completer',
    'ThreadedCompleter',
    'DummyCompleter',
    'DynamicCompleter',
    'CompleteEvent',
    'merge_completers',
    'get_common_complete_suffix',
]


class Completion(object):
    """
    :param text: The new string that will be inserted into the document.
    :param start_position: Position relative to the cursor_position where the
        new text will start. The text will be inserted between the
        start_position and the original cursor position.
    :param display: (optional string) If the completion has to be displayed
        differently in the completion menu.
    :param display_meta: (Optional string) Meta information about the
        completion, e.g. the path or source where it's coming from.
        This can also be a callable that returns a string.
    :param style: Style string.
    :param selected_style: Style string, used for a selected completion.
        This can override the `style` parameter.
    """
    def __init__(self, text, start_position=0, display=None, display_meta=None,
                 style='', selected_style=''):
        assert isinstance(text, text_type)
        assert isinstance(start_position, int)
        assert display is None or isinstance(display, text_type)
        assert display_meta is None or isinstance(display_meta, text_type)
        assert isinstance(style, text_type)
        assert isinstance(selected_style, text_type)

        self.text = text
        self.start_position = start_position
        self._display_meta = display_meta

        if display is None:
            self.display = text
        else:
            self.display = display

        self.style = style
        self.selected_style = selected_style

        assert self.start_position <= 0

    def __repr__(self):
        if self.display == self.text:
            return '%s(text=%r, start_position=%r)' % (
                self.__class__.__name__, self.text, self.start_position)
        else:
            return '%s(text=%r, start_position=%r, display=%r)' % (
                self.__class__.__name__, self.text, self.start_position,
                self.display)

    def __eq__(self, other):
        return (
            self.text == other.text and
            self.start_position == other.start_position and
            self.display == other.display and
            self._display_meta == other._display_meta)

    def __hash__(self):
        return hash((self.text, self.start_position, self.display, self._display_meta))

    @property
    def display_meta(self):
        " Return meta-text. (This is lazy when using a callable). "
        meta = self._display_meta

        if meta is None:
            return ''

        if callable(meta):
            return meta()

        return meta

    def new_completion_from_position(self, position):
        """
        (Only for internal use!)
        Get a new completion by splitting this one. Used by `Application` when
        it needs to have a list of new completions after inserting the common
        prefix.
        """
        assert isinstance(position, int) and position - self.start_position >= 0

        return Completion(
            text=self.text[position - self.start_position:],
            display=self.display,
            display_meta=self._display_meta)


class CompleteEvent(object):
    """
    Event that called the completer.

    :param text_inserted: When True, it means that completions are requested
        because of a text insert. (`Buffer.complete_while_typing`.)
    :param completion_requested: When True, it means that the user explicitly
        pressed the `Tab` key in order to view the completions.

    These two flags can be used for instance to implemented a completer that
    shows some completions when ``Tab`` has been pressed, but not
    automatically when the user presses a space. (Because of
    `complete_while_typing`.)
    """
    def __init__(self, text_inserted=False, completion_requested=False):
        assert not (text_inserted and completion_requested)

        #: Automatic completion while typing.
        self.text_inserted = text_inserted

        #: Used explicitly requested completion by pressing 'tab'.
        self.completion_requested = completion_requested

    def __repr__(self):
        return '%s(text_inserted=%r, completion_requested=%r)' % (
            self.__class__.__name__, self.text_inserted, self.completion_requested)


class Completer(with_metaclass(ABCMeta, object)):
    """
    Base class for completer implementations.
    """
    @abstractmethod
    def get_completions(self, document, complete_event):
        """
        This should be a generator that yields :class:`.Completion` instances.

        If the generation of completions is something expensive (that takes a
        lot of time), consider wrapping this `Completer` class in a
        `ThreadedCompleter`. In that case, the completer algorithm runs in a
        background thread and completions will be displayed as soon as they
        arrive.

        :param document: :class:`~prompt_toolkit.document.Document` instance.
        :param complete_event: :class:`.CompleteEvent` instance.
        """
        while False:
            yield

    def get_completions_async(self, document, complete_event):
        """
        Asynchronous generator for completions. (Probably, you won't have to
        override this.)

        This should return an iterable that can yield both :class:`.Completion`
        and `Future` objects. The :class:`.Completion` objects have to be
        wrapped in a `AsyncGeneratorItem` object.

        If we drop Python 2 support in the future, this could become a true
        asynchronous generator.
        """
        for item in self.get_completions(document, complete_event):
            assert isinstance(item, Completion)
            yield AsyncGeneratorItem(item)


class ThreadedCompleter(Completer):
    """
    Wrapper that runs the `get_completions` generator in a thread.

    (Use this to prevent the user interface from becoming unresponsive if the
    generation of completions takes too much time.)

    The completions will be displayed as soon as they are produced. The user
    can already select a completion, even if not all completions are displayed.
    """
    def __init__(self, completer=None):
        assert isinstance(completer, Completer), 'Got %r' % (completer, )
        self.completer = completer

    def get_completions(self, document, complete_event):
        return self.completer.get_completions(document, complete_event)

    def get_completions_async(self, document, complete_event):
        """
        Asynchronous generator of completions.
        This yields both Future and Completion objects.
        """
        return generator_to_async_generator(
            lambda: self.completer.get_completions(document, complete_event))

    def __repr__(self):
        return 'ThreadedCompleter(%r)' % (self.completer, )


class DummyCompleter(Completer):
    """
    A completer that doesn't return any completion.
    """
    def get_completions(self, document, complete_event):
        return []

    def __repr__(self):
        return 'DummyCompleter()'


class DynamicCompleter(Completer):
    """
    Completer class that can dynamically returns any Completer.

    :param get_completer: Callable that returns a :class:`.Completer` instance.
    """
    def __init__(self, get_completer):
        assert callable(get_completer)
        self.get_completer = get_completer

    def get_completions(self, document, complete_event):
        completer = self.get_completer() or DummyCompleter()
        return completer.get_completions(document, complete_event)

    def get_completions_async(self, document, complete_event):
        completer = self.get_completer() or DummyCompleter()
        return completer.get_completions_async(document, complete_event)

    def __repr__(self):
        return 'DynamicCompleter(%r -> %r)' % (
            self.get_completer, self.get_completer())


class _MergedCompleter(Completer):
    """
    Combine several completers into one.
    """
    def __init__(self, completers):
        assert all(isinstance(c, Completer) for c in completers)
        self.completers = completers

    def get_completions(self, document, complete_event):
        # Get all completions from the other completers in a blocking way.
        for completer in self.completers:
            for c in completer.get_completions(document, complete_event):
                yield c

    def get_completions_async(self, document, complete_event):
        # Get all completions from the other completers in a blocking way.
        for completer in self.completers:
            # Consume async generator -> item can be `AsyncGeneratorItem` or
            # `Future`.
            for item in completer.get_completions_async(document, complete_event):
                yield item


def merge_completers(completers):
    """
    Combine several completers into one.
    """
    return _MergedCompleter(completers)


def get_common_complete_suffix(document, completions):
    """
    Return the common prefix for all completions.
    """
    # Take only completions that don't change the text before the cursor.
    def doesnt_change_before_cursor(completion):
        end = completion.text[:-completion.start_position]
        return document.text_before_cursor.endswith(end)

    completions2 = [c for c in completions if doesnt_change_before_cursor(c)]

    # When there is at least one completion that changes the text before the
    # cursor, don't return any common part.
    if len(completions2) != len(completions):
        return ''

    # Return the common prefix.
    def get_suffix(completion):
        return completion.text[-completion.start_position:]

    return _commonprefix([get_suffix(c) for c in completions2])


def _commonprefix(strings):
    # Similar to os.path.commonprefix
    if not strings:
        return ''

    else:
        s1 = min(strings)
        s2 = max(strings)

        for i, c in enumerate(s1):
            if c != s2[i]:
                return s1[:i]

        return s1
