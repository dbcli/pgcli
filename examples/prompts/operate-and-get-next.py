#!/usr/bin/env python
"""
Demo of "operate-and-get-next".

(Actually, this creates one prompt application, and keeps running the same app
over and over again. -- For now, this is the only way to get this working.)
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import Prompt


def main():
    p = Prompt('prompt> ')
    while True:
        p.prompt()


if __name__ == '__main__':
    main()
