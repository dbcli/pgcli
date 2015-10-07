.. _building_prompts:

Building prompts
================

The following snippet is the most simple example, it uses the
:func:`~prompt_toolkit.shortcuts.prompt` function to asks the user for input
and returns the text. Just like ``(raw_)input``.

.. code:: python

    from __future__ import unicode_literals
    from prompt_toolkit import prompt

    text = prompt('Give me some input: ')
    print('You said: %s' % text)

What we get here is a simple prompt that supports the Emacs key bindings like
readline, but further nothing special. However,
:func:`~prompt_toolkit.shortcuts.prompt` has a lot of configuration options.
In the following sections, we will discover all these parameters.

.. note::

    ``prompt_toolkit`` expects unicode strings everywhere. If you are using
    Python 2, make sure that all strings which are passed to ``prompt_toolkit``
    are unicode strings (and not bytes). Either import ``unicode_literals`` or
    explicitely put a small 'u' in front of every string.


Syntax highlighting
-------------------

Adding syntax highlighting is as simple as adding a lexer. All of the `Pygments
<http://pygments.org/>`_ lexers can be used after wrapping them in a
:class:`~prompt_toolkit.layout.lexers.PygmentsLexer`. It is also possible to
create a custom lexer by implementing the
:class:`~prompt_toolkit.layout.lexers.Lexer` abstract base class.

.. code:: python

    from pygments.lexers import HtmlLexer
    from prompt_toolkit.shortcuts import prompt
    from prompt_toolkit.layout.lexers import PygmentsLexer

    text = prompt('Give me some HTML', lexer=PygmentsLexer(HtmlLexer))
    print('You said: %s' % text)


Colors
------

The colors for syntax highlighting are defined by a Pygments ``Style`` class.
By default, the built-in style :class:`prompt_toolkit.styles.DefaultStyle` is
used, but any Pygments style class can be passed to the
:func:`~prompt_toolkit.shortcuts.prompt` function. Suppose we'd like to use
``pygments.styles.tango.TangoStyle``. That works already, but we would miss
some ``prompt_toolkit`` specific styling, like the highlighting of selected
text and the styling of the completion menus. Because of that, we recommend
creating a custom ``Style`` class, and populate the ``styles`` class attribute
by updating it with the prompt_toolkit extensions.

Creating a custom style could be done like this:

.. code:: python

    from prompt_toolkit.shortcuts import prompt
    from prompt_toolkit.styles import default_style_extensions

    from pygments.style import Style
    from pygments.styles.tango import TangoStyle

    class OurStyle(Style):
        styles = {}
        styles.update(default_style_extensions)
        styles.update(TangoStyle.styles)

    text = prompt('Give me some HTML', lexer=PygmentsLexer(HtmlLexer), style=OurStyle)


Coloring the prompt itself
^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible to add some colors to the prompt itself. For this, we need a
``get_prompt_tokens`` function. This function takes a
:class:`~prompt_toolkit.interface.CommandLineInterface` instance as input
(ignore that for now) and it should return a list of ``(Token, text)`` tuples.
Each token is a Pygments token and can be styled individually.

.. code:: python

    from prompt_toolkit.shortcuts import prompt
    from pygments.style import Style
    from prompt_toolkit.styles import default_style_extensions

    class ExampleStyle(Style):
        styles = {
            # User input.
            Token:          '#ff0066',

            # Prompt.
            Token.Username: '#884444',
            Token.At:       '#00aa00',
            Token.Colon:    '#00aa00',
            Token.Pound:    '#00aa00',
            Token.Host:     '#000088 bg:#aaaaff',
            Token.Path:     '#884444 underline',
        }
        styles.update(default_style_extensions)

    def get_prompt_tokens(cli):
        return [
            (Token.Username, 'john'),
            (Token.At,       '@'),
            (Token.Host,     'localhost'),
            (Token.Colon,    ':'),
            (Token.Path,     '/user/john'),
            (Token.Pound,    '# '),
        ]

    text = prompt(get_prompt_tokens=get_prompt_tokens, style=OurStyle)


Autocompletion
--------------

Autocompletion can be added by passing a ``completer`` parameter. This should
be an instance of the :class:`~prompt_toolkit.completion.Completer` abstract
base class. ``WordCompleter`` is an example of a completer that implements that
interface.

.. code:: python

    from prompt_toolkit import prompt
    from prompt_toolkit.contrib.completers import WordCompleter

    html_completer = WordCompleter(['<html>', '<body>', '<head>', '<title>'])
    text = prompt('Give me some HTML', completer=html_completer)
    print('You said: %s' % text)

``WordCompleter`` is a simple completer that completes the last word before the
cursor with any of the given words.


A custom completer
^^^^^^^^^^^^^^^^^^

For more complex examples, it makes sense to create a custom completer. For
instance:

.. code:: python

    from prompt_toolkit import prompt
    from prompt_toolkit.completion import Completer, Completion

    class MyCustomCompleter(Completer):
        def get_completions(self, document, complete_event):
            yield Completion('completion', start_position=0)

    text = prompt('> ', completer=MyCustomCompleter)

(when ``start_position`` is 0), or it can replace some text before the cursor
(when ``start_position`` is something negative.) The latter makes sense when
:func:`~prompt_toolkit.completion.Completer.get_completions` method. This is a
A Completer class has to implement the
generator that gets the current :class:`~prompt_toolkit.document.Document` and
yields :class:`~prompt_toolkit.completion.Completion` instances, where each
completion contains a portion of text, and the position the completer should be
able to fix for instance casing or typos.  where it should be inserted. It can
insert some text at the current position


Input validation
----------------

A prompt can have a validator attached. This is some code that will check
whether the given input is acceptable and it will only return it if that's the
case. Otherwise it will show an error message and move the cursor to a given
possition.

A validator should implements the :class:`~prompt_toolkit.validation.Validator`
abstract base class. This requires only one method, named ``validate`` that
takes a :class:`~prompt_toolkit.document.Document` as input and raises
:class:`~prompt_toolkit.validation.ValidationError` when the validation fails.

.. code:: python

    from prompt_toolkit.validation import Validator, ValidationError
    from prompt_toolkit import prompt

    class NumberValidator(Validator):
        def validate(self, document):
            text = document.text

            if text and not text.isdigit():
                i = 0

                # Get index of fist non numeric character.
                # We want to move the cursor here.
                for i, c in enumerate(text):
                    if not c.isdigit():
                        break

                raise ValidationError(message='This input contains non-numeric characters',
                                      cursor_position=i)


    number = int(prompt('Give a number: ', validator=NumberValidator()))
    print('You said: %i' % number)


History
-------

A :class:`~prompt_toolkit.history.History` object keeps track of all the
previously entered strings. When nothing is passed into the
:func:`~prompt_toolkit.shortcuts.prompt` function, it will start with an empty
history each time again. Usually, however, for a REPL, you want to keep the
same history between several calls to
:meth:`~prompt_toolkit.shortcuts.prompt`.  This is possible by instantiating a
:class:`~prompt_toolkit.history.History` object and passing that to each
``prompt`` call.


.. code:: python

    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit import prompt

    history = InMemoryHistory()

    while True:
        prompt(history=history)


To persist a history to disk, use :class:`~prompt_toolkit.history.FileHistory`
instead instead of :class:`~prompt_toolkit.history.InMemoryHistory`.


Auto suggestion
---------------

Auto suggestion is a way to propose some input completions to the user like the
`fish shell <http://fishshell.com/>`_.

Usually, the input is compared to the history and when there is another entry
starting with the given text, the completion will be shown as gray text behind
the current input. Pressing the right arrow will insert this suggestion.

.. note:: 

    When suggestions are based on the history, don't forget to share one
    :class:`~prompt_toolkit.history.History` object between consecutive
    :func:`~prompt_toolkit.shortcuts.prompt` calls.

Example:

.. code:: python

    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

    while True:
        text = prompt('> ', history=history, auto_suggest=AutoSuggestFromHistory())
        print('You said: %s' % text)


A suggestion does not have to come from the history. Any implementation of the
:class:`~prompt_toolkit.auto_suggest.AutoSuggest` abstract base class can be
passed as an argument.


Vi input mode
-------------

Prompt-toolkit supports both Emacs and Vi key bindings, similar to Readline.
The :func:`~prompt_toolkit.shortcuts.prompt` function will use Emacs bindings by
default. This is done because on most operating systems, also the Bash shell
uses Emacs bindings by default, and that is more intuitive. If however, Vi
binding are required, just pass ``vi_mode=True``.

.. code:: python

    from prompt_toolkit import prompt

    prompt('> ', vi_mode=True)


Adding custom key bindings
--------------------------

The :func:`~prompt_toolkit.shortcuts.prompt` function accepts an optional
``key_bindings_registry`` argument. This should be
a :class:`~prompt_toolkit.key_binding.registry.Registry` instance which hold
all of the key bindings.

It would be possible to create such a
:class:`~prompt_toolkit.key_binding.registry.Registry` class ourself, but
usually, for a prompt, we would like to have at least the basic (Emacs/Vi)
bindings and start from there. That's what the
:class:`~prompt_toolkit.key_binding.manager.KeyBindingManager` class does.

An example of a prompt that prints 'hello world' when Control-T is pressed.

.. code:: python

    from prompt_toolkit import prompt
    from prompt_toolkit.key_binding.manager import KeyBindingManager
    from prompt_toolkit.keys import Keys

    manager = KeyBindingManager.for_prompt()

    @manager.registry.add_binding(Keys.ControlT)
    def _(event):
        def print_hello():
            print('hello world')
        event.cli.run_in_terminal(print_hello)

    text = prompt('> ', key_bindings_registry=manager.registry)
    print('You said: %s' % text)


Note that we use
:meth:`~prompt_toolkit.interface.CommandLineInterface.run_in_terminal`. This
ensures that the output of the print-statement and the prompt don't mix up.


Other prompt options
--------------------

Multiline input
^^^^^^^^^^^^^^^

Reading multiline input is as easy as passing the ``multiline=True`` parameter.

.. code:: python

    from prompt_toolkit import prompt

    prompt('> ', multiline=True)

A side effect of this is that the enter key will now insert a newline instead
of accepting and returning the input. The user will now have to press
``Meta+Enter`` in order to accept the input. (Or ``Escape`` folowed by
``Enter``.)


Passing a default
^^^^^^^^^^^^^^^^^

A default value can be given:

.. code:: python

    from prompt_toolkit import prompt
    import getpass

    prompt('What is your name: ', default='%s' % getpass.getuser())


Mouse support
^^^^^^^^^^^^^

There is limited mouse support for positioning the cursor, for scrolling (in
case of large multiline inputs) and for clicking in the autocompletion menu.

Enabling can be done by passing the ``mouse_support=True`` option.

.. code:: python

    from prompt_toolkit import prompt
    import getpass

    prompt('What is your name: ', mouse_support=True)


Line wrapping
^^^^^^^^^^^^^

Line wrapping is enabled by default. This is what most people are used too and
this is what GNU readline does. When it is disabled, the input string will
scroll horizontally.

.. code:: python

    from prompt_toolkit import prompt
    import getpass

    prompt('What is your name: ', wrap_lines=False)


Password input
^^^^^^^^^^^^^^

When the ``is_password=True`` flag has been given, the input is replaced by
asterisks (``*`` characters).

.. code:: python

    from prompt_toolkit import prompt
    import getpass

    prompt('What is your name: ', is_password=True)
