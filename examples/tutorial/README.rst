Build a REPL With Python Prompt Toolkit
---------------------------------------

The aim of this tutorial is to build an interactive command line interface for
SQLite database using prompt_toolkit_.

prompt_toolkit_ is an easy to use library for building powerful command
lines (REPLs) in Python.


First install the library using pip.

::

    pip install prompt_toolkit

Let's get started!

#. Read User Input

   Start accepting input using the ``get_input()`` method.

   .. code:: python

       from prompt_toolkit.shortcuts import get_input

       def main():
           text = get_input("> ")
           print('You entered:', text)

       if __name__ == '__main__':
           main()

   .. image :: screenshots/1.png

#. Loop The REPL

   Now we call the ``get_input`` method in a loop while keeeping the line
   history in our ``History`` object.

   .. code:: python

       from prompt_toolkit.shortcuts import get_input
       from prompt_toolkit.history import History

       def main():
           history = History()

           while True:
               text = get_input("> ", history=history)
               print('You entered:', text)
           print('GoodBye!')

       if __name__ == '__main__':
           main()

   .. image :: screenshots/2.png

#. Syntax Highlighting

   So far we've been doing really basic stuff, let's step it up a notch by
   adding syntax highlighting to the user input. We know that users will be
   entering sql statements, so let's leverage the Pygments_ library for
   coloring the input.  The ``lexer`` param allow you to set the syntax lexer.
   We're going to use the ``SqlLexer`` from the Pygments_ library for
   highlighting.

   .. code:: python

       from prompt_toolkit.shortcuts import get_input
       from prompt_toolkit.history import History
       from pygments.lexers import SqlLexer

       def main():
           history = History()

           while True:
               text = get_input('> ', lexer=SqlLexer, history=history)
               print('You entered:', text)
           print('GoodBye!')

       if __name__ == '__main__':
           main()

   .. image :: screenshots/3.png

#. Auto-completion

   OMG! Syntax highlighting is awesome! You know what's awesomer!?
   Auto-completion! Let's do that.

   Create your ``sql_completer`` instance from the ``WordCompleter`` class
   defining a set of ``keywords`` for auto-completion.

   This ``sql_completer`` instance will be passed into the ``get_input``
   function.

   .. code:: python

       from prompt_toolkit.shortcuts import get_input
       from prompt_toolkit.history import History
       from prompt_toolkit.contrib.completers import WordCompleter
       from pygments.lexers import SqlLexer

       sql_completer = WordCompleter(['create', 'select', 'insert', 'drop',
                                      'delete', 'from', 'where', 'table'], ignore_case=True)


       def main():
           history = History()

           while True:
               text = get_input('> ', lexer=SqlLexer, completer=sql_completer, history=history)
               print('You entered:', text)
           print('GoodBye!')

       if __name__ == '__main__':
           main()

   .. image :: screenshots/4.png

   In about 30 lines of code we got ourselves an autocompleting, syntax
   highlighting REPL. Let's make it better.

#. Styling the menus

   The completion menu is hard to see, so let's add some customization to the
   menu colors. Create a class named ``DocumentStyle`` and sub-class it from
   ``pygments.style``. Customize the colors for the completion menu and pass in
   the style as a parameter to the ``get_input`` function.

   .. code:: python

       from prompt_toolkit.shortcuts import get_input
       from prompt_toolkit.history import History
       from prompt_toolkit.contrib.completers import WordCompleter
       from pygments.lexers import SqlLexer
       from pygments.style import Style
       from pygments.token import Token
       from pygments.styles.default import DefaultStyle

       sql_completer = WordCompleter(['create', 'select', 'insert', 'drop',
                                      'delete', 'from', 'where', 'table'], ignore_case=True)

       class DocumentStyle(Style):
           styles = {
               Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
               Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
               Token.Menu.Completions.ProgressButton: 'bg:#003333',
               Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
           }
           styles.update(DefaultStyle.styles)

       def main():
           history = History()

           while True:
               text = get_input('> ', lexer=SqlLexer, completer=sql_completer, style=DocumentStyle, history=history)
               print('You entered:', text)
           print('GoodBye!')

       if __name__ == '__main__':
           main()

   .. image :: screenshots/5.png

   All that's left is hooking up the sqlite backend, which is left as an
   exercise for the reader. Just kidding... keep reading.

#. Hook up Sqlite

   This step is totally optional ;). So far we've been focusing on building the
   REPL. Now it's time to relay the input to SQLite.

   Obviously I haven't done the due diligence to deal with the errors. But it
   gives you an idea of how to get started.

   .. code:: python

       import sys
       import sqlite3

       from prompt_toolkit.shortcuts import get_input
       from prompt_toolkit.history import History
       from prompt_toolkit.contrib.completers import WordCompleter
       from pygments.lexers import SqlLexer
       from pygments.style import Style
       from pygments.token import Token
       from pygments.styles.default import DefaultStyle

       sql_completer = WordCompleter(['create', 'select', 'insert', 'drop',
                                      'delete', 'from', 'where', 'table'], ignore_case=True)

       class DocumentStyle(Style):
           styles = {
               Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
               Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
               Token.Menu.Completions.ProgressButton: 'bg:#003333',
               Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
           }
           styles.update(DefaultStyle.styles)

       def main(database):
           history = History()
           connection = sqlite3.connect(database)

           while True:
               try:
                   text = get_input('> ', lexer=SqlLexer, completer=sql_completer, style=DocumentStyle, history=history,
                                    on_abort=AbortAction.RETRY)
               except EOFError:
                   break  # Control-D pressed.
               with connection:
                   messages = connection.execute(text)
                   for message in messages:
                       print(message)
           print('GoodBye!')

       if __name__ == '__main__':
           if len(sys.argv) < 2:
               db = ':memory:'
           else:
               db = sys.argv[1]

           main(db)

   .. image :: screenshots/6.png

I hope that gives an idea of how to get started on building CLIs.

The End.

.. _prompt_toolkit: https://github.com/jonathanslenders/python-prompt-toolkit
.. _Pygments: http://pygments.org/
