from __future__ import unicode_literals


class IncrementalSearchDirection:
    FORWARD = 'forward'
    BACKWARD = 'backward'


#: Name of the search buffer.
SEARCH_BUFFER = 'search'

#: Name of the default buffer.
DEFAULT_BUFFER = 'default'

#: Name of the system buffer.
SYSTEM_BUFFER = 'system'

# Dummy buffer. This is the buffer returned by
# `CommandLineInterface.current_buffer` when the top of the `FocusStack` is
# `None`. This could be the case when there is some widget has the focus and no
# actual text editing is possible. This buffer should also never be displayed.
# (It will never contain any actual text.)
DUMMY_BUFFER = 'dummy'
