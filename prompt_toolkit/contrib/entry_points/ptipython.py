#!/usr/bin/env python
"""
ptipython: IPython interactive shell with the `prompt_toolkit` front-end.
Usage:
    ptpython [ --vi ] [ --history=<filename> ]
             [ --autocompletion=<type> ] [ --always-multiline ]
             [--] [ <file> <arg>... ]
    ptpython -h | --help

Options:
    --vi                    : Use Vi keybindings instead of Emacs bindings.
    --history=<filename>    : Path to history file.
"""
import docopt
import os
import six
import sys


def run():
    a = docopt.docopt(__doc__)

    vi_mode = bool(a['--vi'])

    # If IPython is not available, show message and exit here with error status
    # code.
    try:
        import IPython
    except ImportError:
        print('IPython not found. Please install IPython (pip install ipython).')
        sys.exit(1)
    else:
        from prompt_toolkit.contrib.ipython import embed

    # Log history
    if a['--history']:
        history_filename = os.path.expanduser(a['--history'])
    else:
        history_filename = os.path.expanduser('~/.ptpython_history')

    # Add the current directory to `sys.path`.
    sys.path.append('.')

    # When a file has been given, run that, otherwise start the shell.
    if a['<file>']:
        sys.argv = [a['<file>']] + a['<arg>']
        six.exec_(compile(open(a['<file>'], "rb").read(), a['<file>'], 'exec'))
    else:
        # Create an empty namespace for this interactive shell. (If we don't do
        # that, all the variables from this function will become available in
        # the IPython shell.)
        user_ns = {}

        # Run interactive shell.
        embed(vi_mode=vi_mode, history_filename=history_filename, user_ns=user_ns)


if __name__ == '__main__':
    run()
