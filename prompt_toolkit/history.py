"""
Implementations for the history of a `Buffer`.

NOTE: Notice that there is no `DynamicHistory`. This doesn't work well, because
      the `Buffer` needs to be able to attach an event handler to the event
      when a history entry is loaded. This loading can be done asynchronously
      and making the history swappable would probably break this.
"""
from __future__ import unicode_literals

from .utils import Event
from .eventloop import AsyncGeneratorItem, From, ensure_future, consume_async_generator, generator_to_async_generator

from abc import ABCMeta, abstractmethod
from six import with_metaclass, text_type

import datetime
import os

__all__ = [
    'History',
    'ThreadedHistory',
    'DummyHistory',
    'FileHistory',
    'InMemoryHistory',
]


class History(with_metaclass(ABCMeta, object)):
    """
    Base ``History`` class.

    This also includes abstract methods for loading/storing history.
    """
    def __init__(self):
        # In memory storage for strings.
        self._loading = False
        self._loaded_strings = []
        self._item_loaded = Event(self)

    def _start_loading(self):
        """
        Consume the asynchronous generator: `load_history_strings_async`.

        This is only called once, because once the history is loaded, we don't
        have to load it again.
        """
        def add_string(string):
            " Got one string from the asynchronous history generator. "
            self._loaded_strings.insert(0, string)
            self._item_loaded.fire()

        yield From(consume_async_generator(
            self.load_history_strings_async(),
            cancel=lambda: False,  # Right now, we don't have cancellation
                                   # of history loading in any way.
            item_callback=add_string))

    #
    # Methods expected by `Buffer`.
    #

    def start_loading(self):
        " Start loading the history. "
        if not self._loading:
            self._loading = True
            ensure_future(self._start_loading())

    def get_item_loaded_event(self):
        " Event which is triggered when a new item is loaded. "
        return self._item_loaded

    def get_strings(self):
        """
        Get the strings from the history that are loaded so far.
        """
        return self._loaded_strings

    def append_string(self, string):
        " Add string to the history. "
        self._loaded_strings.append(string)
        self.store_string(string)

    #
    # Implementation for specific backends.
    #

    @abstractmethod
    def load_history_strings(self):
        """
        This should be a generator that yields `str` instances.

        It should yield the most recent items first, because they are the most
        important. (The history can already be used, even when it's only
        partially loaded.)
        """
        while False:
            yield

    def load_history_strings_async(self):
        """
        Asynchronous generator for history strings. (Probably, you won't have
        to override this.)

        This should return an iterable that can yield both `str`
        and `Future` objects. The `str` objects have to be
        wrapped in a `AsyncGeneratorItem` object.

        If we drop Python 2 support in the future, this could become a true
        asynchronous generator.
        """
        for item in self.load_history_strings():
            assert isinstance(item, text_type)
            yield AsyncGeneratorItem(item)

    @abstractmethod
    def store_string(self, string):
        """
        Store the string in persistent storage.
        """


class ThreadedHistory(History):
    """
    Wrapper that runs the `load_history_strings` generator in a thread.

    Use this to increase the start-up time of prompt_toolkit applications.
    History entries are available as soon as they are loaded. We don't have to
    wait for everything to be loaded.
    """
    def __init__(self, history=None):
        assert isinstance(history, History), 'Got %r' % (history, )
        self.history = history
        super(ThreadedHistory, self).__init__()

    def load_history_strings_async(self):
        """
        Asynchronous generator of completions.
        This yields both Future and Completion objects.
        """
        return generator_to_async_generator(
            self.history.load_history_strings)

    # All of the following are proxied to `self.history`.

    def load_history_strings(self):
        return self.history.load_history_strings()

    def store_string(self, string):
        self.history.store_string(string)

    def __repr__(self):
        return 'ThreadedHistory(%r)' % (self.history, )


class InMemoryHistory(History):
    """
    :class:`.History` class that keeps a list of all strings in memory.
    """
    def load_history_strings(self):
        return []

    def store_string(self, string):
        pass


class DummyHistory(History):
    """
    :class:`.History` object that doesn't remember anything.
    """
    def load_history_strings(self):
        return []

    def store_string(self, string):
        pass

    def append_string(self, string):
        # Don't remember this.
        pass


class FileHistory(History):
    """
    :class:`.History` class that stores all strings in a file.
    """
    def __init__(self, filename):
        self.filename = filename
        super(FileHistory, self).__init__()

    def load_history_strings(self):
        strings = []
        lines = []

        def add():
            if lines:
                # Join and drop trailing newline.
                string = ''.join(lines)[:-1]

                strings.append(string)

        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                for line in f:
                    line = line.decode('utf-8')

                    if line.startswith('+'):
                        lines.append(line[1:])
                    else:
                        add()
                        lines = []

                add()

        # Reverse the order, because newest items have to go first.
        return reversed(strings)

    def store_string(self, string):
        # Save to file.
        with open(self.filename, 'ab') as f:
            def write(t):
                f.write(t.encode('utf-8'))

            write('\n# %s\n' % datetime.datetime.now())
            for line in string.split('\n'):
                write('+%s\n' % line)
