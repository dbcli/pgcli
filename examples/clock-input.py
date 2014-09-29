#!/usr/bin/env python
"""
Example of a 'dynamic' prompt. On that shows the current time in the prompt.
"""
from prompt_toolkit import CommandLineInterface
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import Prompt
from pygments.token import Token

import datetime
import time


class ClockPrompt(Prompt):
    def tokens(self, cli):
        now = datetime.datetime.now()
        return [
            (Token.Prompt, '%s:%s:%s' % (now.hour, now.minute, now.second)),
            (Token.Prompt, ' Enter something: ')
        ]


def main():
    cli = CommandLineInterface(layout=Layout(before_input=ClockPrompt()))

    def on_read_start():
        """
        This function is called when we start reading at the input.
        (Actually the start of the read-input event loop.)
        """
        # Following function should be run in the background.
        # We do it by using an executor thread from the `CommandLineInterface`
        # instance.
        def run():
            # Send every second a redraw request.
            while cli.is_reading_input:
                time.sleep(1)
                cli.request_redraw()

        cli.run_in_executor(run)
    cli.onReadInputStart += on_read_start

    code_obj = cli.read_input()
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
