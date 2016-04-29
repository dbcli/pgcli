#!/usr/bin/env python
from __future__ import unicode_literals

from buffer_tests import *
from contrib_tests import *
from document_tests import *
from inputstream_tests import *
from key_binding_tests import *
from layout_tests import *
from regular_languages_tests import *
from style_tests import *
from utils_tests import *
from filter_tests import *
from cli_tests import *

import unittest

# Import modules for syntax checking.
import prompt_toolkit
import prompt_toolkit.application
import prompt_toolkit.auto_suggest
import prompt_toolkit.buffer
import prompt_toolkit.buffer_mapping
import prompt_toolkit.clipboard
import prompt_toolkit.completion
import prompt_toolkit.contrib.completers
import prompt_toolkit.contrib.regular_languages
import prompt_toolkit.contrib.telnet
import prompt_toolkit.contrib.validators
import prompt_toolkit.document
import prompt_toolkit.enums
import prompt_toolkit.eventloop.base
import prompt_toolkit.eventloop.inputhook
import prompt_toolkit.eventloop.posix
import prompt_toolkit.eventloop.posix_utils
import prompt_toolkit.eventloop.utils
import prompt_toolkit.filters.base
import prompt_toolkit.filters.cli
import prompt_toolkit.filters.types
import prompt_toolkit.filters.utils
import prompt_toolkit.history
import prompt_toolkit.input
import prompt_toolkit.interface
import prompt_toolkit.key_binding
import prompt_toolkit.keys
import prompt_toolkit.layout
import prompt_toolkit.output
import prompt_toolkit.reactive
import prompt_toolkit.renderer
import prompt_toolkit.search_state
import prompt_toolkit.selection
import prompt_toolkit.shortcuts
import prompt_toolkit.styles
import prompt_toolkit.terminal
import prompt_toolkit.terminal.vt100_input
import prompt_toolkit.terminal.vt100_output
import prompt_toolkit.utils
import prompt_toolkit.validation

if __name__ == '__main__':
    unittest.main()
