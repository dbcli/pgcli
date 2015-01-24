"""
DEPRECATED.
"""
from __future__ import unicode_literals

__all__ = ('PythonRepl', 'embed')


def embed(*a, **kw):
    """
    DEPRECATED. Only for backwards compatibility.
    Please call ptpython.repl.embed directly!
    """
    try:
        import ptpython.repl
        ptpython.repl.embed(*a, **kw)
    except ImportError as e:
        print('prompt_toolkit was installed, but could not find ptpython.')
        print('Please run: "pip install ptpython"')
        raise e
