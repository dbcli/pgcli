from __future__ import unicode_literals
from functools import wraps


def create_handle_decorator(registry, filter):
    """
    Create a key handle decorator, which is compatible with `Registry.handle`
    but has a `save_before` option, which will make sure that undo changes are
    saved to the undo stack of the `Buffer` object before every key press
    event.
    """
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


def focus_next_buffer(cli, name_filter=None, _previous=False):
    """
    Move the focus to the next buffer.
    (We only consider buffers for which the focussable filter returns True.)
    """
    # Exclude buffers with these names.
    if cli.current_buffer.focussable(cli):
        # Find next buffer.
        buffer_names = [name for name, buffer in cli.buffers.items()
                        if buffer.focussable(cli)]
        if name_filter:
            buffer_names = [n for n in buffer_names if name_filter(n)]

        buffer_names = sorted(buffer_names)

        # Reverse in case of previous.
        if _previous:
            buffer_names = buffer_names[::-1]

        index = buffer_names.index(cli.focus_stack.current)
        new_index = (index + 1) % len(buffer_names)

        # Replace focus.
        cli.focus_stack.replace(buffer_names[new_index])


def focus_previous_buffer(cli, name_filter=None):
    return focus_next_buffer(cli, name_filter=name_filter, _previous=True)
