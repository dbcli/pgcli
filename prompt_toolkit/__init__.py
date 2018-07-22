"""
prompt_toolkit
==============

Author: Jonathan Slenders

Description: prompt_toolkit is a Library for building powerful interactive
             command lines in Python.  It can be a replacement for GNU
             Readline, but it can be much more than that.

See the examples directory to learn about the usage.

Probably, to get started, you might also want to have a look at
`prompt_toolkit.shortcuts.prompt`.
"""
from __future__ import unicode_literals
from .application import Application
from .shortcuts import PromptSession, prompt, print_formatted_text
from .formatted_text import HTML, ANSI


# Don't forget to update in `docs/conf.py`!
__version__ = '2.0.4'


__all__ = [
    # Application.
    'Application',

    # Shortcuts.
    'prompt',
    'PromptSession',
    'print_formatted_text',

    # Formatted text.
    'HTML', 'ANSI',
]
