"""
prompt_toolkit
==============

Author: Jonathan Slenders

Description: prompt_toolkit is a Library for building powerful interactive
             command lines in Python.  It can be a replacement for GNU
             readline, but it can be much more than that.

See the examples directory to learn about the usage.

Probably, to get started, you meight also want to have a lookt at
`prompt_toolkit.shortcuts.get_input`.
"""
from .interface import CommandLineInterface
from .application import AbortAction, Application
