#!/usr/bin/env python
"""
Demo of "operate-and-get-next".

(Actually, this creates one prompt application, and keeps running the same app
over and over again. -- For now, this is the only way to get this working.)
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import create_prompt_application, run_application


def main():
    app = create_prompt_application('prompt> ')
    while True:
        run_application(app)


if __name__ == '__main__':
    main()
