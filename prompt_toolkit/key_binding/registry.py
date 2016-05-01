from __future__ import unicode_literals
from ..filters import CLIFilter, to_cli_filter, Never
from ..keys import Key

from six import text_type
from six.moves import range
from collections import defaultdict

__all__ = (
    'Registry',
)


class _Binding(object):
    """
    (Immutable binding class.)
    """
    def __init__(self, keys, handler, filter=None, eager=None, invalidate_ui=True):
        assert isinstance(keys, tuple)
        assert callable(handler)
        assert isinstance(filter, CLIFilter)
        assert isinstance(eager, CLIFilter)
        assert isinstance(invalidate_ui, CLIFilter)

        self.keys = keys
        self.handler = handler
        self.filter = filter
        self.eager = eager
        self.invalidate_ui = invalidate_ui

    def call(self, event):
        return self.handler(event)

    def __repr__(self):
        return '%s(keys=%r, handler=%r)' % (
            self.__class__.__name__, self.keys, self.handler)


class Registry(object):
    """
    Key binding registry.

    ::

        r = Registry()

        @r.add_binding(Keys.ControlX, Keys.ControlC, filter=INSERT)
        def handler(event):
            # Handle ControlX-ControlC key sequence.
            pass
    """
    def __init__(self):
        self.key_bindings = []

        #: (tuple of keys) -> [list of bindings handling this sequence].
        self._keys_to_bindings = defaultdict(list)

        #: (tuple of keys) -> [list of bindings handling suffixes of this sequence].
        self._keys_to_bindings_suffixes = defaultdict(list)

    def add_binding(self, *keys, **kwargs):
        """
        Decorator for annotating key bindings.

        :param filter: :class:`~prompt_toolkit.filters.CLIFilter` to determine
            when this key binding is active.
        :param eager: :class:`~prompt_toolkit.filters.CLIFilter` or `bool`.
            When True, ignore potential longer matches when this key binding is
            hit. E.g. when there is an active eager key binding for Ctrl-X,
            execute the handler immediately and ignore the key binding for
            Ctrl-X Ctrl-E of which it is a prefix.
        :param invalidate_ui: :class:`~prompt_toolkit.filters.CLIFilter` or
            `bool`. When True (which is the default), invalidate (redraw) the
            user interface after handling this key binding.
        """
        filter = to_cli_filter(kwargs.pop('filter', True))
        eager = to_cli_filter(kwargs.pop('eager', False))
        invalidate_ui = to_cli_filter(kwargs.pop('invalidate_ui', True))

        assert not kwargs
        assert keys
        assert all(isinstance(k, (Key, text_type)) for k in keys), \
            'Key bindings should consist of Key and string (unicode) instances.'

        def decorator(func):
            # When a filter is Never, it will always stay disabled, so in that case
            # don't bother putting it in the registry. It will slow down every key
            # press otherwise. (This happens for instance when a KeyBindingManager
            # is used, but some set of bindings are always disabled.)
            if not isinstance(filter, Never):
                binding = _Binding(keys, func, filter=filter, eager=eager,
                                   invalidate_ui=invalidate_ui)

                self.key_bindings.append(binding)
                self._keys_to_bindings[keys].append(binding)

                for i in range(1, len(keys)):
                    self._keys_to_bindings_suffixes[keys[:i]].append(binding)

            return func
        return decorator

    def remove_binding(self, function):
        """
        Remove a key binding.

        This expects a function that was given to `add_binding` method as
        parameter. Raises `ValueError` when the given function was not
        registered before.
        """
        assert callable(function)

        for b in self.key_bindings:
            if b.handler == function:
                self.key_bindings.remove(b)
                self._keys_to_bindings[b.keys].remove(b)

                for i in range(1, len(b.keys)):
                    self._keys_to_bindings_suffixes[b.keys[:i]].remove(b)

                return

        # No key binding found for this function. Raise ValueError.
        raise ValueError('Binding not found: %r' % (function, ))

    def get_bindings_for_keys(self, keys):
        """
        Return a list of key bindings that can handle this key.
        (This return also inactive bindings, so the `filter` still has to be
        called, for checking it.)

        :param keys: tuple of keys.
        """
        return self._keys_to_bindings[keys]

    def get_bindings_starting_with_keys(self, keys):
        """
        Return a list of key bindings that handle a key sequence starting with
        `keys`. (It does only return bindings for which the sequences are
        longer than `keys`. And like `get_bindings_for_keys`, it also includes
        inactive bindings.)

        :param keys: tuple of keys.
        """
        return self._keys_to_bindings_suffixes[keys]
