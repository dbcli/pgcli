#!/usr/bin/env python
"""
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.python_input import PythonCommandLineInterface


def main():
    cli = PythonCommandLineInterface()

    code_obj = cli.read_input()
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
