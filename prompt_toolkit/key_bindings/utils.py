from __future__ import unicode_literals


def create_handle_decorator(registry, line):
    """
    Create a key handle decorator, which is compatible with `Registry.handle`
    but has a `save_before` option, which will make sure that undo changes are
    saved to the undo stack of the `Line` object before every key press event.
    """
    def handle(*keys, **kw):
        safe_before = kw.pop('save_before', True)

        def decorator(handler_func):
            @registry.add_binding(*keys, **kw)
            def wrapper(event):
                if safe_before:
                    line.save_to_undo_stack()
                handler_func(event)
            return handler_func
        return decorator
    return handle
