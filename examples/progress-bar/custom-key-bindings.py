#!/usr/bin/env python
"""
A very simple progress bar which keep track of the progress as we consume an
iterator.
"""
from __future__ import unicode_literals
from prompt_toolkit import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import ProgressBar

import time
import os
import signal


def main():
    bottom_toolbar = HTML(' <b>[f]</b> Print "f" <b>[q]</b> Abort  <b>[x]</b> Send Control-C.')

    # Create custom key bindings first.
    kb = KeyBindings()
    cancel = [False]

    @kb.add('f')
    def _(event):
        print('You pressed `f`.')

    @kb.add('q')
    def _(event):
        " Quit by setting cancel flag. "
        cancel[0] = True

    @kb.add('x')
    def _(event):
        " Quit by sending SIGINT to the main thread. "
        os.kill(os.getpid(), signal.SIGINT)

    # Use `patch_stdout`, to make sure that prints go above the
    # application.
    with patch_stdout():
        with ProgressBar(key_bindings=kb, bottom_toolbar=bottom_toolbar) as pb:
            for i in pb(range(800)):
                time.sleep(.01)

                if cancel[0]:
                    break


if __name__ == '__main__':
    main()
