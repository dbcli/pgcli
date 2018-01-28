from __future__ import unicode_literals
from .base import Output, DummyOutput
from .defaults import create_output, get_default_output, set_default_output

__all__ = [
    # Base.
    'Output',
    'DummyOutput',

    # Defaults.
    'create_output',
    'get_default_output',
    'set_default_output',
]
