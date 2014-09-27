from __future__ import unicode_literals


class IncrementalSearchDirection:
    FORWARD = 'forward'
    BACKWARD = 'backward'


class InputMode(object):
    INSERT = 'vi-insert'

    VI_NAVIGATION = 'vi-navigation'
    VI_REPLACE = 'vi-replace'

    # Selection mode. The type of selection (characters/lines/block is saved in
    # the line object.)
    SELECTION = 'selection'

    #: Ctrl-R/Ctrl-S incremental search.
    INCREMENTAL_SEARCH = 'incremental-search'

    #: Vi-style forward search. Usually with a '/' or '?' prompt.
    VI_SEARCH = 'vi-forward-search'

    #: When the system prompt (after typing '!' or M-!) has the focus.
    SYSTEM = 'system'
