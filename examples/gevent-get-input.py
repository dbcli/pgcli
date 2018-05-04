#!/usr/bin/env python
"""
For testing: test to make sure that everything still works when gevent monkey
patches are applied.
"""
from __future__ import unicode_literals
from gevent.monkey import patch_all
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.eventloop.defaults import create_event_loop


if __name__ == '__main__':
    # Apply patches.
    patch_all()

    # There were some issues in the past when the event loop had an input hook.
    def dummy_inputhook(*a):
        pass
    eventloop = create_event_loop(inputhook=dummy_inputhook)

    # Ask for input.
    session = PromptSession('Give me some input: ', loop=eventloop)
    answer = session.prompt()
    print('You said: %s' % answer)
