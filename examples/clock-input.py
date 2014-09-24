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



class ClockCLI(CommandLineInterface):
    def on_read_input_start(self):
        self.run_in_executor(self._clock_update)

    def _clock_update(self):
        # Send every second a redraw request.
        while self.is_reading_input:
            time.sleep(1)
            self.request_redraw()


def main():
    cli = ClockCLI(layout=Layout(before_input=ClockPrompt()))

    code_obj = cli.read_input()
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
