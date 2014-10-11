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

   Create an object of type ``prompt_toolkit.CommandLineInterface`` and start
   accepting input using the ``read_input()`` method. This is similar to the
   python's ``raw_input()`` method.

   .. code:: python

       from prompt_toolkit import CommandLineInterface

       def main():
           cli = CommandLineInterface()
           document = cli.read_input()
           print 'You entered:', document.text

       if __name__ == '__main__':
           main()

   .. image :: screenshots/1.png

#. Loop The REPL

   The ``read_input`` method takes a kwarg called ``on_exit`` that dictates
   what happens when ``^D`` is pressed. ``AbortAction`` is a class that provides
   various opitons and we've chosen to throw an exception called ``Exit``. This
   exception is caught in the except clause to quit the program.

   .. code:: python

       from prompt_toolkit import CommandLineInterface, AbortAction, Exit

       def main():
           cli = CommandLineInterface()
           try:
               while True:
                   document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                   print 'You entered:', document.text
           except Exit:
               print 'GoodBye!'

       if __name__ == '__main__':
           main()

   .. image :: screenshots/2.png

#. Syntax Highlighting

   So far we've been doing really basic stuff, let's step it up a notch by
   adding syntax highlighting to the user input. We know that users will be
   entering sql statements, so let's leverage the Pygments_ library for
   coloring the input.  The ``prompt_toolkit.layout`` class is responsible for
   how the REPL is displayed. This allows us to customize the prompt and choose
   a lexer for syntax.  We're going to use the ``SqlLexer`` from the Pygments_
   library for highlighting.

   .. code:: python

       from prompt_toolkit import CommandLineInterface, AbortAction, Exit
       from prompt_toolkit.layout import Layout
       from prompt_toolkit.layout.prompt import DefaultPrompt
       from pygments.lexers import SqlLexer

       def main():
           layout = Layout(before_input=DefaultPrompt('> '), lexer=SqlLexer)
           cli = CommandLineInterface(layout=layout)
           try:
               while True:
                   document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                   print 'You entered:', document.text
           except Exit:
               print 'GoodBye!'

       if __name__ == '__main__':
           main()

   .. image :: screenshots/3.png

#. Auto-completion

   OMG! Syntax highlighting is awesome! You know what's awesomer!?
   Auto-completion! Let's do that.

   Create a class called ``SqlCompleter`` that is derived from
   ``prompt_toolkit.Completer``. Define a set of ``keywords`` for
   auto-completion. Override the `get_completions`` method to
   populate the completion menu with possible candidates from the list
   of ``keywords``.

   This ``SqlCompleter`` class will be passed into the ``prompt_toolkit.Line`` class
   which controls the cusor position and completion of a line.

   .. code:: python

       from prompt_toolkit import CommandLineInterface, AbortAction, Exit
       from prompt_toolkit.layout import Layout
       from prompt_toolkit.line import Line
       from prompt_toolkit.layout.prompt import DefaultPrompt
       from prompt_toolkit.layout.menus import CompletionsMenu
       from prompt_toolkit.completion import Completion, Completer
       from pygments.lexers import SqlLexer

       class SqlCompleter(Completer):
           keywords = ['create', 'select', 'insert', 'drop',
                       'delete', 'from', 'where', 'table']

           def get_completions(self, document, complete_event):
               word_before_cursor = document.get_word_before_cursor()

               for keyword in self.keywords:
                   if keyword.startswith(word_before_cursor):
                       yield Completion(keyword, -len(word_before_cursor))

       def main():
           layout = Layout(before_input=DefaultPrompt('> '),
                           lexer=SqlLexer, menus=[CompletionsMenu()])
           line = Line(completer=SqlCompleter())
           cli = CommandLineInterface(layout=layout, line=line)
           try:
               while True:
                   document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                   print 'You entered:', document.text
           except Exit:
               print 'GoodBye!'

       if __name__ == '__main__':
           main()

   .. image :: screenshots/4.png

   In about 30 lines of code we got ourselves an autocompleting, syntax
   highlighting REPL. Let's make it better.

#. Styling the menus

   The completion menu is hard to see, so let's add some customization to the
   menu colors. Create a class named ``DocumentStyle`` and sub-class it from
   ``pygments.style``. Customize the colors for the completion menu and pass in
   the style as a parameter to the ``CommandLineInterface`` constructor.

   .. code:: python

       from prompt_toolkit import CommandLineInterface, AbortAction, Exit
       from prompt_toolkit.layout import Layout
       from prompt_toolkit.line import Line
       from prompt_toolkit.layout.prompt import DefaultPrompt
       from prompt_toolkit.layout.menus import CompletionsMenu
       from prompt_toolkit.completion import Completion, Completer
       from pygments.lexers import SqlLexer
       from pygments.style import Style
       from pygments.token import Token
       from pygments.styles.default import DefaultStyle

       class SqlCompleter(Completer):
           keywords = ['create', 'select', 'insert', 'drop',
                       'delete', 'from', 'where', 'table']

           def get_completions(self, document, complete_event):
               word_before_cursor = document.get_word_before_cursor()

               for keyword in self.keywords:
                   if keyword.startswith(word_before_cursor):
                       yield Completion(keyword, -len(word_before_cursor))

       class DocumentStyle(Style):
           styles = {
               Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
               Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
               Token.Menu.Completions.ProgressButton: 'bg:#003333',
               Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
           }
           styles.update(DefaultStyle.styles)

       def main():
           layout = Layout(before_input=DefaultPrompt('> '),
                           lexer=SqlLexer, menus=[CompletionsMenu()])
           line = Line(completer=SqlCompleter())
           cli = CommandLineInterface(style=DocumentStyle, layout=layout, line=line)
           try:
               while True:
                   document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                   print 'You entered:', document.text
           except Exit:
               print 'GoodBye!'

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

       from prompt_toolkit import CommandLineInterface, AbortAction, Exit
       from prompt_toolkit.layout import Layout
       from prompt_toolkit.line import Line
       from prompt_toolkit.layout.prompt import DefaultPrompt
       from prompt_toolkit.layout.menus import CompletionsMenu
       from prompt_toolkit.completion import Completion, Completer
       from pygments.lexers import SqlLexer
       from pygments.style import Style
       from pygments.token import Token
       from pygments.styles.default import DefaultStyle

       class SqlCompleter(Completer):
           keywords = ['create', 'select', 'insert', 'drop',
                       'delete', 'from', 'where', 'table']

           def get_completions(self, document, complete_event):
               word_before_cursor = document.get_word_before_cursor()

               for keyword in self.keywords:
                   if keyword.startswith(word_before_cursor):
                       yield Completion(keyword, -len(word_before_cursor))

       class DocumentStyle(Style):
           styles = {
               Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
               Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
               Token.Menu.Completions.ProgressButton: 'bg:#003333',
               Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
           }
           styles.update(DefaultStyle.styles)

       def main(database):
           connection = sqlite3.connect(database)
           layout = Layout(before_input=DefaultPrompt('> '),
                           lexer=SqlLexer, menus=[CompletionsMenu()])
           line = Line(completer=SqlCompleter())
           cli = CommandLineInterface(style=DocumentStyle, layout=layout, line=line)
           try:
               while True:
                   document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                   with connection:
                       messages = connection.execute(document.text)
                       for message in messages:
                           print message
           except Exit:
               print 'GoodBye!'

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
