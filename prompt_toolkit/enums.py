from __future__ import unicode_literals

class LineMode(object):
    """
    State of the `Line` object.
    """
    #: Ready for inserting text, or navigation.
    NORMAL = 'normal'

    #: Ctrl-R/Ctrl-S incremental search.
    INCREMENTAL_SEARCH = 'incremental-search'

    #: Ctrl-N/Ctrl-P style navigation through completions.
    COMPLETE = 'complete'


class IncrementalSearchDirection:
    FORWARD = 'forward'
    BACKWARD = 'backward'
