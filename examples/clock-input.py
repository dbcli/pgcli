#!/usr/bin/env python
"""
Example of a 'dynamic' prompt. On that shows the current time in the prompt.
"""
from __future__ import unicode_literals
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.processors import Processor
from prompt_toolkit.layout.utils import token_list_len
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.utils import Callback
from pygments.token import Token

import datetime
import time


class ClockPrompt(Processor):
    def run(self, cli, buffer, tokens):
        now = datetime.datetime.now()
        before = [
            (Token.Prompt, '%s:%s:%s' % (now.hour, now.minute, now.second)),
            (Token.Prompt, ' Enter something: ')
        ]

        return before + tokens, lambda i: i + token_list_len(before)

    def invalidation_hash(self, cli, buffer):
        return datetime.datetime.now()


def main():
    eventloop = create_eventloop()
    done = [False]  # Non local

    def on_read_start(cli):
        """
        This function is called when we start reading at the input.
        (Actually the start of the read-input event loop.)
        """
        # Following function should be run in the background.
        # We do it by using an executor thread from the `CommandLineInterface`
        # instance.
        def run():
            # Send every second a redraw request.
            while not done[0]:
                time.sleep(1)
                cli.request_redraw()

        cli.eventloop.run_in_executor(run)

    def on_read_end(cli):
        done[0] = True

    app = Application(
        layout=Window(BufferControl(input_processors=[ClockPrompt()])),
        on_start=Callback(on_read_start),
        on_stop=Callback(on_read_end))

    cli = CommandLineInterface(application=app, eventloop=eventloop)

    code_obj = cli.run()
    print('You said: %s' % code_obj.text)

    eventloop.close()


if __name__ == '__main__':
    main()
