Python Prompt Toolkit
=====================

|Build Status|

``prompt_toolkit`` is a Library for building powerful interactive command lines
in Python. It ships with a nice interactive Python shell (called ``ptpython``)
built on top of the library.

``prompt_toolkit`` could be a replacement for ``readline``, but it can be much
more than that.

Features:

- Pure Python.
- Syntax highlighting of the input while typing. (For instance, with a Pygments lexer.)
- Multi-line input editing.
- Advanced code completion.
- Both Emacs and Vi key bindings. (Similar to readline.)
- Reverse and forward incremental search.
- Both Python 3 and Python 2.7 support.
- Works well with Unicode double width characters. (Chinese input.)
- Selecting text for copy/paste. (Both Emacs and Vi style.)
- No global state.
- Code written with love.
- Runs on Linux, OS X, OpenBSD and Windows systems.


Feel free to create tickets for bugs and feature requests, and create pull
requests if you have a nice patches that you would like to share with others.

About Windows support
*********************

``prompt_toolkit`` is cross platform, and everything that you build on top
should run fine on both Unix and Windows systems. On Windows, it uses a
different event loop (``WaitForMultipleObjects`` instead of ``select``), and
another input and output system. (Win32 APIs instead of pseudo-terminals and
VT100.)

.. image :: docs/images/ptpython-windows.png


That should work fine, however the library is currently much more tested on
Linux and Mac os X systems. So, if you find any bugs in the Windows
implementation, or you have an idea how to make the experience better, please
create a Github issue.

It's worth noting that the implementation is a "best effort of what is
possible". Both Unix and Windows terminals have their limitations. But in
general, the Unix experience will still be a little better.


Installation
------------

::

    pip install prompt-toolkit


The Python repl
---------------

Run ``ptpython`` to get an interactive Python prompt with syntax highlighting,
code completion, etc...

.. image :: docs/images/ptpython-screenshot.png

If you prefer to have Vi key bindings (which currently are more completely
implemented than the Emacs bindings), run ``ptpython --vi``.

If you want to embed the REPL inside your application at one point, do:

.. code:: python

    from prompt_toolkit.contrib.repl import embed
    embed(globals(), locals(), vi_mode=False, history_filename=None)

Autocompletion
**************

``Tab`` and ``shift+tab`` complete the input. (Thanks to the `Jedi
<http://jedi.jedidjah.ch/en/latest/>`_ autocompletion library.)
In Vi-mode, you can also use ``Ctrl+N`` and ``Ctrl+P``.

.. image :: docs/images/ptpython-complete-menu.png


Multiline editing
*****************

Usually, multi-line editing mode will automatically turn on when you press enter
after a colon, however you can always turn it on by pressing ``F7``.

To execute the input in multi-line mode, you can either press ``Alt+Enter``, or
``Esc`` followed by ``Enter``. (If you want the first to work in the OS X
terminal, you have to check the "Use option as meta key" checkbox in your
terminal settings. For iTerm2, you have to check "Left option acts as +Esc" in
the options.)

Other features
***************

Running system commands: Press ``Meta-!`` in Emacs mode or just ``!`` in Vi
navigation mode to see the "Shell command" prompt. There you can enter system
commands without leaving the REPL.

Selecting text: Press ``Control+Space`` in Emacs mode on ``V`` (major V) in Vi
navigation mode.

You love IPython?
*****************

Run ``ptipython`` (prompt_toolkit - IPython), to get a nice interactive shell
with all the power that IPython has to offer, like magic functions and shell
integration. Make sure that IPython has been installed. (``pip install
ipython``)

.. image :: docs/images/ipython-integration.png

You are using Django?
*********************

`django-extensions <https://github.com/django-extensions/django-extensions>`_
has a ``shell_plus`` management command. When ``prompt_toolkit`` has been
installed, it will by default use ``ptpython`` or ``ptipython``.


Using as a library
------------------

This is a library which allows you to build highly customizable input prompts.
Every step (key bindings, layout, etc..) can be customized.

Note that this is work in progress. Many things work, but code is still
refactored a lot and APIs can change (they will become even better), so be
prepared to handle these changes.

Certainly look in the ``examples`` directory to see what is possible.

A very simple example:

.. code:: python

    from prompt_toolkit import CommandLineInterface, AbortAction
    from prompt_toolkit import Exit

    def main():
        cli = CommandLineInterface()

        try:
            while True:
                code_obj = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                print('You said: ' + code_obj.text)

        except Exit: # Quit on Ctrl-D keypress
            return

    if __name__ == '__main__':
        main()


FAQ
---

Q
 The ``Ctrl-S`` forward search doesn't work and freezes my terminal.
A
 Try to run ``stty -ixon`` in your terminal to disable flow control.

Q
 The ``Meta``-key doesn't work.
A
 For some terminals you have to enable the Alt-key to act as meta key, but you
 can also type ``Escape`` before any key instead.


Special thanks to
-----------------

- `Pygments <http://pygments.org/>`_: Syntax highlighter.
- `Jedi <http://jedi.jedidjah.ch/en/latest/>`_: Autocompletion library.
- `Docopt <http://docopt.org/>`_: Command-line interface description language.
- `wcwidth <https://github.com/jquast/wcwidth>`_: Determine columns needed for a wide characters.


.. |Build Status| image:: https://travis-ci.org/jonathanslenders/python-prompt-toolkit.png
    :target: https://travis-ci.org/jonathanslenders/python-prompt-toolkit#
