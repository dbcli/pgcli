.. documentation master file, created by
   sphinx-quickstart on Thu Jul 31 14:17:08 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Python Prompt Toolkit
=====================

`prompt_toolkit` is a Library for building interactive command lines in Python.

It could be a replacement for `readline`. It's Pure Python, and has some
advanced features:

- Syntax highlighting of the input while typing. (Usually with a Pygments lexer.)
- Multiline input
- Advanced code completion
- Both Emacs and Vi keybindings (Similar to readline), including
  reverse and forward incremental search


On top of that, it implements `prompt_toolkit.shell`, a library for shell-like
interfaces. You can define the grammar of the input string, ...

Thanks to:

 - Pygments
 - wcwidth
 -

 Chapters
 --------

 - Simple example. (Most simple example, alternative to raw_input.)
 - Architecture of a line
 -

.. toctree::
   :maxdepth: 3

   pages/example
   pages/repl
   pages/architecture
   pages/reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

