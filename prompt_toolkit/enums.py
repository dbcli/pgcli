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

    # Selection mode. The type of selection (characters/lines/block is saved in
    # the line object.)
    SELECTION = 'selection'

    #: Ctrl-R/Ctrl-S incremental search.
    INCREMENTAL_SEARCH = 'incremental-search'

    #: Ctrl-N/Ctrl-P style navigation through completions.
    COMPLETE = 'complete'
