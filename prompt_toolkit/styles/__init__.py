"""
Styling for prompt_toolkit applications.
"""
from __future__ import unicode_literals

from .base import *
from .defaults import *
from .from_dict import *
from .from_pygments import *
from .utils import *


#: The default built-in style.
DEFAULT_STYLE = style_from_dict(DEFAULT_STYLE_DICTIONARY)
