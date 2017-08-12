Python Prompt Toolkit
=====================

`prompt_toolkit` is a library for building powerful interactive command lines
and terminal applications in Python.


It can be a pure Python replacement for `GNU readline
<http://cnswww.cns.cwru.edu/php/chet/readline/rltop.html>`_, but it can be much
more than that.

Some features:

- Syntax highlighting of the input while typing. (For instance, with a Pygments lexer.)
- Multi-line input editing.
- Advanced code completion.
- Selecting text for copy/paste. (Both Emacs and Vi style.)
- Mouse support for cursor positioning and scrolling.
- Auto suggestions. (Like `fish shell <http://fishshell.com/>`_.)
- No global state.

Like readline:

- Both Emacs and Vi key bindings.
- Reverse and forward incremental search.
- Works well with Unicode double width characters. (Chinese input.)

Works everywhere:

- Pure Python. Runs on all Python versions from 2.6 up to 3.4.
- Runs on Linux, OS X, OpenBSD and Windows systems.
- Lightweight, the only dependencies are Pygments, six and wcwidth.
- No assumptions about I/O are made. Every prompt_toolkit application should
  also run in a telnet/ssh server or an `asyncio
  <https://docs.python.org/3/library/asyncio.html>`_ process.


Two use cases: prompts versus full screen terminal applications
---------------------------------------------------------------

``prompt_toolkit`` was in the first place meant to be a replacement for
readline. However, when it became more mature, we realised that all the
components for full screen applications are there and ``prompt_toolkit`` is
very capable of handling many use cases. `Pyvim
<http://github.com/jonathanslenders/pyvim>`_ and `pymux
<http://github.com/jonathanslenders/pymux>`_ are examples of full screen
applications.

.. image:: images/pyvim.png

Basically, at the core, ``prompt_toolkit`` has a layout engine, that supports
horizontal and vertical splits as well as floats, where each "window" can
display a user control. The API for user controls is simple yet powerful.

When ``prompt_toolkit`` is used to simply read some input from the user, it
uses a rather simple built-in layout. One that displays the default input
buffer and the prompt, a float for the autocompletions and a toolbar for input
validation which is hidden by default.

For full screen applications, usually we build the layout ourself, because it's
very custom.

Further, there is a very flexible key binding system that can be programmed for
all the needs of full screen applications.


Installation
------------

::

    pip install prompt_toolkit

For Conda, do:

::

    conda install -c https://conda.anaconda.org/conda-forge prompt_toolkit


Getting started
---------------

The following snippet is the most simple example, it uses the
:func:`~prompt_toolkit.prompt` function to asks the user for input
and returns the text. Just like ``(raw_)input``.

.. code:: python

    from __future__ import unicode_literals
    from prompt_toolkit import prompt

    text = prompt('Give me some input: ')
    print('You said: %s' % text)

For more information, start reading the :ref:`building prompts
<building_prompts>` section.


Thanks to:
----------

Thanks to `all the contributors
<https://github.com/jonathanslenders/python-prompt-toolkit/graphs/contributors>`_
for making prompt_toolkit possible.

Also, a special thanks to the `Pygments <http://pygments.org/>`_ and `wcwidth
<https://github.com/jquast/wcwidth>`_ libraries.


Table of contents
-----------------

.. toctree::
   :maxdepth: 3

   pages/gallery
   pages/printing_text
   pages/building_prompts
   pages/dialogs
   pages/full_screen_apps
   pages/architecture
   pages/reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Prompt_toolkit was created by `Jonathan Slenders
<http://github.com/jonathanslenders/>`_.
