Python Prompt Toolkit
=====================

`prompt_toolkit` is a library for building powerful interactive command lines
in Python.


It can be a pure Python replacement for `GNU readline
<http://cnswww.cns.cwru.edu/php/chet/readline/rltop.html>`_, but it can be much
more than that.

Some features:

- Syntax highlighting of the input while typing. (For instance, with a Pygments lexer.)
- Multi-line input editing.
- Advanced code completion.
- Both Emacs and Vi key bindings. (Similar to readline.)
- Reverse and forward incremental search.
- Runs on all Python versions from 2.6 up to 3.4.
- Works well with Unicode double width characters. (Chinese input.)
- Selecting text for copy/paste. (Both Emacs and Vi style.)
- Multiple input buffers.
- No global state.
- Lightweight, the only dependencies are Pygments, six and wcwidth.
- Code written with love.
- Runs on Linux, OS X, OpenBSD and Windows systems.


Installation
---------------

::

    pip install prompt_toolkit


Getting started
---------------

The following snippet is the most simple example, it uses the
:func:`~prompt_toolkit.shortcuts.get_input` function to asks the user for input
and returns the text. Just like ``(raw_)input``.

.. code:: python

    from prompt_toolkit.shortcuts import get_input

    text = get_input('Give me some input: ')
    print('You said: %s' % text)

Let's add some highlighting to the input. We like to highlight HTML. It's very
simple, just use one of the many lexers that `Pygments <http://pygments.org/>`_
provides.

.. code:: python

    from pygments.lexers import HtmlLexer
    from prompt_toolkit.shortcuts import get_input

    text = get_input('Give me some HTML', lexer=HtmlLexer)
    print('You said: %s' % text)

Finally, let's add autocompletion:

.. code:: python

    from pygments.lexers import HtmlLexer
    from prompt_toolkit.shortcuts import get_input
    from prompt_toolkit.contrib.completers import WordCompleter

    html_completer = WordCompleter(['<html>', '<body>', '<head>', '<title>'])
    text = get_input('Give me some HTML', lexer=HtmlLexer, completer=html_completer)
    print('You said: %s' % text)


Chapters
--------

TODO: these chapters still have to be written:

 - Simple example. (Most simple example, alternative to raw_input.)
 - Architecture of an application

 - Prompts.
 - Colors (styles.)
 - Autocompletion
 - Key bindings.
 - Input validation.
 - Input hooks.
 - History.
 - Layouts.

 - contrib.regular_languages
 - contrib.telnet.
 - asyncio


Thanks to:
----------

 - Pygments
 - wcwidth


Table of contents
-----------------

.. toctree::
   :maxdepth: 3

   pages/example
   pages/architecture
   pages/reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
