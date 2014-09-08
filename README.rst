Python Prompt Toolkit
=====================

(Work in progress. Many things work, but APIs can change.)


``prompt_toolkit`` is a Library for building powerful interactive command lines
in Python. It ships with a nice interative Python shell (called ``ptpython``)
built on top of the library.

``prompt_toolkit`` can be a replacement for ``readline``.

Features:

- Pure Python.
- Syntax highlighting of the input while typing. (For instance, with a Pygments lexer.)
- Multiline input editing.
- Advanced code completion.
- Both Emacs and Vi keybindings. (Similar to readline.)
- Reverse and forward incremental search.
- Both Python 3 and Python 2.7 support.
- Works well with Unicode double width characters. (Chinese input.)
- No global state.
- Code written with love.


Limitations:

- Only for vt100-compatible terminals. (Actually, all terminals in OS X and
  Linux systems are VT100 compatible the days, so that should not be an issue.
  There is no Windows support, however.)


Installation
------------

::

    pip install prompt-toolkit


The Python repl
---------------

Run ``ptpython`` to get an interactive Python prompt with syntaxt highlighting,
code completion, etc...

.. image :: docs/images/ptpython-screenshot.png

If you prefer to have Vi keybindings (which currently are more completely
implemented than the Emacs bindings), run ``ptpython --vi``.

If you want to embed the repl inside your application at one point, do:

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

Usually, multiline editing mode will automatically turn on when you press enter
after a colon, however you can always turn it on by pressing ``F7``.

To execute the input in multiline mode, you can either press ``Alt+Enter``, or
``Esc`` followed by ``Enter``. (If you want the first to work in the OS X
terminal, you have to check the "Use option as meta key" checkbox in your
terminal settings. For iTerm2, you have to check "Left option acts as +Esc" in
the options.)


You love IPython?
*****************

Run ``ptipython`` (prompt_toolkit - IPython), to get a nice interactive shell
with all the power that IPython has to offer, like magic functions and shell
integration.

.. image :: docs/images/ipython-integration.png


Using as a library
------------------

This is a library which allows you to build highly customizable input prompts.
Every step (from key bindings, to line behaviour until the renderer can be
customized.)

A simple example looks like this:

.. code:: python

    from prompt_toolkit import CommandLine, AbortAction
    from prompt_toolkit.line import Exit

    def main():
        # Create CommandLine instance
        cli = CommandLine()

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

Q: The ``Ctrl-S`` forward search doesn't work and freezes my terminal.
A: Try to run ``stty -ixon`` in your terminal to disable flow control.

Q: The ``Meta``-key doesn't work.
A: For some terminals you have to enable the Alt-key to act as enum key, but
   you can also type ``Escape`` before any key instead.


Special thanks to
-----------------

- `Pygments <http://pygments.org/>`_: Syntax highlighter.
- `Jedi <http://jedi.jedidjah.ch/en/latest/>`_: Autocompletion library.
