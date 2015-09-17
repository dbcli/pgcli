from __future__ import unicode_literals
from functools import wraps
from prompt_toolkit.filters import CLIFilter, Always

__all__ = (
    'create_handle_decorator',
)

def create_handle_decorator(registry, filter=Always()):
    """
    Create a key handle decorator, which is compatible with `Registry.handle`
    but has a `save_before` option, which will make sure that changes are saved
    to the undo stack of the `Buffer` object before every key press event.

    :param save_before: Callable that takes an `Event` and returns True if we
        should save the current buffer, before handling the event. (That's the
        default.)
    """
    assert isinstance(filter, CLIFilter)

    def handle(*keys, **kw):
        save_before = kw.pop('save_before', lambda e: True)

        # Chain the given filter to the filter of this specific binding.
        if 'filter' in kw:
            kw['filter'] = kw['filter'] & filter
        else:
            kw['filter'] = filter

        def decorator(handler_func):
            @registry.add_binding(*keys, **kw)
            @wraps(handler_func)
            def wrapper(event):
                if save_before(event):
                    event.cli.current_buffer.save_to_undo_stack()
                handler_func(event)
            return handler_func
        return decorator
    return handle
