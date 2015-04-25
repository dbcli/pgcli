from __future__ import unicode_literals
from functools import wraps
from prompt_toolkit.filters import CLIFilter, Always


def create_handle_decorator(registry, filter=Always()):
    """
    Create a key handle decorator, which is compatible with `Registry.handle`
    but has a `save_before` option, which will make sure that undo changes are
    saved to the undo stack of the `Buffer` object before every key press
    event.
    """
    assert isinstance(filter, CLIFilter)

    def handle(*keys, **kw):
        safe_before = kw.pop('save_before', True)

        # Chain the given filter to the filter of this specific binding.
        if 'filter' in kw:
            kw['filter'] = kw['filter'] & filter
        else:
            kw['filter'] = filter

        def decorator(handler_func):
            @registry.add_binding(*keys, **kw)
            @wraps(handler_func)
            def wrapper(event):
                if safe_before:
                    event.cli.current_buffer.save_to_undo_stack()
                handler_func(event)
            return handler_func
        return decorator
    return handle
