#!/usr/bin/env python
"""
Simple example of a CLI that keeps a persistent history of all the entered
strings in a file.
"""
from prompt_toolkit import CommandLineInterface, AbortAction, Exit
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.history import FileHistory


def main():
    cli = CommandLineInterface(
        buffer=Buffer(history=FileHistory('.example-history-file')))

    try:
        while True:
            document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
            print('You said: ' + document.text)
    except Exit:
        pass


if __name__ == '__main__':
    main()
