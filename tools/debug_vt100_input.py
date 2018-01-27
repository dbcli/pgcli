#!/usr/bin/env python
"""
Parse vt100 input and print keys.
For testing terminal input.
"""
from __future__ import unicode_literals
import sys

from prompt_toolkit.input.vt100 import raw_mode
from prompt_toolkit.input.vt100_parser import Vt100Parser
from prompt_toolkit.keys import Keys


def callback(key_press):
    print(key_press)

    if key_press.key == Keys.ControlC:
        sys.exit(0)


def main():
    stream = Vt100Parser(callback)

    with raw_mode(sys.stdin.fileno()):
        while True:
            c = sys.stdin.read(1)
            stream.feed(c)


if __name__ == '__main__':
    main()
