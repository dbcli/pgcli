from __future__ import unicode_literals


class IncrementalSearchDirection:
    FORWARD = 'forward'
    BACKWARD = 'backward'


class InputMode(object):
    INPUT = 'input'
    EMACS = 'emacs'

    VI_NAVIGATION = 'vi-navigation'
    VI_INSERT = 'vi-insert'
    VI_REPLACE = 'vi-replace'

    # TODO: Not supported. But maybe for some day...
    VI_VISUAL = 'vi-visual'
    VI_VISUAL_LINE = 'vi-visual-line'
    VI_VISUAL_BLOCK = 'vi-visual-block'

    #: Ctrl-R/Ctrl-S incremental search.
    INCREMENTAL_SEARCH = 'incremental-search'

    #: Ctrl-N/Ctrl-P style navigation through completions.
    COMPLETE = 'complete'
