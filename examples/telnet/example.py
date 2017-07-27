#!/usr/bin/env python
from __future__ import unicode_literals

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.eventloop import From, get_event_loop
from prompt_toolkit.layout.lexers import PygmentsLexer

from pygments.lexers import HtmlLexer

import logging

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def interact(connection):
    # When a client is connected, erase the screen from the client and say
    # Hello.
    connection.erase_screen()
    connection.send('Welcome!\n')

    # Set CommandLineInterface.
    animal_completer = WordCompleter(['alligator', 'ant'])

    result = yield From(connection.prompt_async(
        message='Say something: ',
        lexer=PygmentsLexer(HtmlLexer),
        completer=animal_completer))

    connection.send('You said: {}\n'.format(result))


    connection.send('Say something else:\n')
    result = yield From(connection.prompt_async(message='>: '))
    connection.send('You said: %s\n' % result)

    connection.send('Bye.\n')


def main():
    server = TelnetServer(interact=interact, port=2323)
    server.start()
    get_event_loop().run_forever()


if __name__ == '__main__':
    main()
