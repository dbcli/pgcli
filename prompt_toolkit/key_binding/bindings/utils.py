from __future__ import unicode_literals
from prompt_toolkit.filters import CLIFilter, Always

__all__ = (
    'create_handle_decorator',
)

def create_handle_decorator(registry, filter=Always()):
    """
    Create a key handle decorator, which is compatible with `Registry.handle`,
    but will chain the given filter to every key binding.

    :param filter: `CLIFilter`
    """
    assert isinstance(filter, CLIFilter)

    def handle(*keys, **kw):
        # Chain the given filter to the filter of this specific binding.
        if 'filter' in kw:
            kw['filter'] = kw['filter'] & filter
        else:
            kw['filter'] = filter

        return registry.add_binding(*keys, **kw)
    return handle
