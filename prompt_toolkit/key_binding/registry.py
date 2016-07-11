from __future__ import unicode_literals
from prompt_toolkit.cache import SimpleCache
from prompt_toolkit.filters import CLIFilter, to_cli_filter, Never
from prompt_toolkit.keys import Key, Keys

from six import text_type

__all__ = (
    'Registry',
)


class _Binding(object):
    """
    (Immutable binding class.)
    """
    def __init__(self, keys, handler, filter=None, eager=None, save_before=None):
        assert isinstance(keys, tuple)
        assert callable(handler)
        assert isinstance(filter, CLIFilter)
        assert isinstance(eager, CLIFilter)
        assert callable(save_before)

        self.keys = keys
        self.handler = handler
        self.filter = filter
        self.eager = eager
        self.save_before = save_before

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
        self._get_bindings_for_keys_cache = SimpleCache(maxsize=10000)
        self._get_bindings_starting_with_keys_cache = SimpleCache(maxsize=1000)

    def _clear_cache(self):
        self._get_bindings_for_keys_cache.clear()
        self._get_bindings_starting_with_keys_cache.clear()

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
        :param save_before: Callable that takes an `Event` and returns True if
            we should save the current buffer, before handling the event.
            (That's the default.)
        """
        filter = to_cli_filter(kwargs.pop('filter', True))
        eager = to_cli_filter(kwargs.pop('eager', False))
        save_before = kwargs.pop('save_before', lambda e: True)
        to_cli_filter(kwargs.pop('invalidate_ui', True))  # Deprecated! (ignored.)

        assert not kwargs
        assert keys
        assert all(isinstance(k, (Key, text_type)) for k in keys), \
            'Key bindings should consist of Key and string (unicode) instances.'
        assert callable(save_before)

        if isinstance(filter, Never):
            # When a filter is Never, it will always stay disabled, so in that case
            # don't bother putting it in the registry. It will slow down every key
            # press otherwise.
            def decorator(func):
                return func
        else:
            def decorator(func):
                self.key_bindings.append(
                    _Binding(keys, func, filter=filter, eager=eager,
                             save_before=save_before))
                self._clear_cache()

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
                self._clear_cache()
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
        def get():
            result = []
            for b in self.key_bindings:
                if len(keys) == len(b.keys):
                    match = True
                    any_count = 0

                    for i, j in zip(b.keys, keys):
                        if i != j and i != Keys.Any:
                            match = False
                            break

                        if i == Keys.Any:
                            any_count += 1

                    if match:
                        result.append((any_count, b))

            # Place bindings that have more 'Any' occurences in them at the end.
            result = sorted(result, key=lambda item: -item[0])

            return [item[1] for item in result]

        return self._get_bindings_for_keys_cache.get(keys, get)

    def get_bindings_starting_with_keys(self, keys):
        """
        Return a list of key bindings that handle a key sequence starting with
        `keys`. (It does only return bindings for which the sequences are
        longer than `keys`. And like `get_bindings_for_keys`, it also includes
        inactive bindings.)

        :param keys: tuple of keys.
        """
        def get():
            result = []
            for b in self.key_bindings:
                if len(keys) < len(b.keys):
                    match = True
                    for i, j in zip(b.keys, keys):
                        if i != j and i != Keys.Any:
                            match = False
                            break
                    if match:
                        result.append(b)
            return result

        return self._get_bindings_starting_with_keys_cache.get(keys, get)
