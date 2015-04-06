from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'EventLoopCallbacks',
)


class EventLoopCallbacks(with_metaclass(ABCMeta, object)):
    """
    ``EventLoopCallbacks`` is the glue between the eventloops and
    ``CommandLineInterface`` instances.

    The ``loop`` method of an eventloop takes a ``EventLoopCallbacks`` instance
    and operates on that one, driving the interface.
    """
    @abstractmethod
    def terminal_size_changed(self):
        pass

    @abstractmethod
    def input_timeout(self):
        pass

    @abstractmethod
    def feed_key(self, key):
        pass

    @abstractmethod
    def redraw(self):
        pass
