"""
Abstraction of CLI Input.
"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod, abstractproperty
from six import with_metaclass

__all__ = [
    'Input',
    'DummyInput',
]


class Input(with_metaclass(ABCMeta, object)):
    """
    Abstraction for any input.

    An instance of this class can be given to the constructor of a
    :class:`~prompt_toolkit.application.Application` and will also be
    passed to the :class:`~prompt_toolkit.eventloop.base.EventLoop`.
    """
    @abstractmethod
    def fileno(self):
        """
        Fileno for putting this in an event loop.
        """

    @abstractmethod
    def typeahead_hash(self):
        """
        Identifier for storing type ahead key presses.
        """

    @abstractmethod
    def read_keys(self):
        """
        Return a list of Key objects which are read/parsed from the input.
        """

    def flush_keys(self):
        """
        Flush the underlying parser. and return the pending keys.
        (Used for vt100 input.)
        """
        return []

    def flush(self):
        " The event loop can call this when the input has to be flushed. "
        pass

    @property
    def responds_to_cpr(self):
        """
        `True` if the `Application` can expect to receive a CPR response from
        here.
        """
        return False

    @abstractproperty
    def closed(self):
        " Should be true when the input stream is closed. "
        return False

    @abstractmethod
    def raw_mode(self):
        """
        Context manager that turns the input into raw mode.
        """

    @abstractmethod
    def cooked_mode(self):
        """
        Context manager that turns the input into cooked mode.
        """

    @abstractmethod
    def attach(self, input_ready_callback):
        """
        Return a context manager that makes this input active in the current
        event loop.
        """

    @abstractmethod
    def detach(self):
        """
        Return a context manager that makes sure that this input is not active
        in the current event loop.
        """

    def close(self):
        " Close input. "
        pass


class DummyInput(Input):
    """
    Input for use in a `DummyApplication`
    """
    def fileno(self):
        raise NotImplementedError

    def typeahead_hash(self):
        return 'dummy-%s' % id(self)

    def read_keys(self):
        return []

    @property
    def closed(self):
        return True

    def raw_mode(self):
        raise NotImplementedError

    def cooked_mode(self):
        raise NotImplementedError

    def attach(self, input_ready_callback):
        raise NotImplementedError

    def detach(self):
        raise NotImplementedError
