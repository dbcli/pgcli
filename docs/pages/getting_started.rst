.. _getting_started:

Getting started
===============

Installation
------------

::

    pip install prompt_toolkit

For Conda, do:

::

    conda install -c https://conda.anaconda.org/conda-forge prompt_toolkit


Several use cases: prompts versus full screen terminal applications
--------------------------------------------------------------------

`prompt_toolkit` was in the first place meant to be a replacement for readline.
However, when it became more mature, we realised that all the components for
full screen applications are there and `prompt_toolkit` is very capable of
handling many use situations. `Pyvim
<http://github.com/jonathanslenders/pyvim>`_ and `pymux
<http://github.com/jonathanslenders/pymux>`_ are examples of full screen
applications.

.. image:: ../images/pyvim.png

Basically, at the core, `prompt_toolkit` has a layout engine, that supports
horizontal and vertical splits as well as floats, where each "window" can
display a user control. The API for user controls is simple yet powerful.

When `prompt_toolkit` is used as a readline replacement, (to simply read some
input from the user), it uses a rather simple built-in layout. One that
displays the default input buffer and the prompt, a float for the
autocompletions and a toolbar for input validation which is hidden by default.

For full screen applications, usually we build a custom layout ourselves.

Further, there is a very flexible key binding system that can be programmed for
all the needs of full screen applications.


A simple prompt
---------------

The following snippet is the most simple example, it uses the
:func:`~prompt_toolkit.shortcuts.prompt` function to asks the user for input
and returns the text. Just like ``(raw_)input``.

.. code:: python

    from __future__ import unicode_literals
    from prompt_toolkit import prompt

    text = prompt('Give me some input: ')
    print('You said: %s' % text)


Learning `prompt_toolkit`
-------------------------

In order to learn and understand `prompt_toolkit`, it is best to go through the
all sections in the order below. Also don't forget to have a look at all the
examples `examples
<https://github.com/jonathanslenders/python-prompt-toolkit/tree/master/examples>`_
in the repository.

- First, :ref:`learn how to print text <printing_text>`. This is important,
  because it covers how to use "formatted text", which is something you'll use
  whenever you want to use colors anywhere.

- Secondly, go through the :ref:`asking for input <asking_for_input>` section.
  This is useful for almost any use case, even for full screen applications.
  It covers autocompletions, syntax highlighting, key bindings, and so on.

- Then, learn about :ref:`dialogs`, which is easy and fun.

- Finally, learn about :ref:`full screen applications
  <full_screen_applications>` and read through :ref:`the advanced topics
  <advanced_topics>`.
