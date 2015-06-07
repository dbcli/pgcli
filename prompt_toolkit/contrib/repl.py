"""
DEPRECATED.
"""
from __future__ import unicode_literals

__all__ = ('embed', )


# We have this for compatibility with older versions of:
# django_extensions.management.commands.shell_plus
try:
    import ptpython.repl

    def embed(*a, **kw):
        """
        DEPRECATED. Only for backwards compatibility.
        Please call ptpython.repl.embed directly!
        """
        ptpython.repl.embed(*a, **kw)
except ImportError as e:
    pass
