Examples
========

Let's start with a simple command line prompt to just retrieve input from the
user. It's very simple:

.. code:: python

    from prompt_toolkit.shortcuts import get_input

    answer = get_input('Give me some input: ')
    print('You said: %s' % answer)

What we get here is a prompt that supports the Emacs key bindings like
readline, but further nothing special. However, ``get_input`` has a lot of
options to enhence the prompt. Have a look at
:func:`~prompt_toolkit.shortcuts.get_input`.

We will now discover all of the parameters that
:func:`~prompt_toolkit.shortcuts.get_input` accepts to customize this prompt.
