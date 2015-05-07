Python Prompt Toolkit
=====================

|Build Status|  |PyPI|

``prompt_toolkit`` is a library for building powerful interactive command lines
in Python.

Looking for ptpython, the Python REPL?
**************************************

Are you looking for ``ptpython``, the interactive Python Shell? We moved the
``ptpython`` source code to a separate repository. This way we are sure not to
pollute the ``prompt_toolkit`` library with any ``ptpython``-specific stuff and
``ptpython`` can be developed independently. You will now have to install it
through::

    pip install ptpython

`Go to ptpython... <http://github.com/jonathanslenders/ptpython/>`_

.. image :: https://github.com/jonathanslenders/python-prompt-toolkit/raw/master/docs/images/ptpython.png

prompt-toolkit features
***********************

``prompt_toolkit`` could be a replacement for `GNU readline
<http://cnswww.cns.cwru.edu/php/chet/readline/rltop.html>`_, but it can be much
more than that.

Some features:

- Pure Python.
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

Feel free to create tickets for bugs and feature requests, and create pull
requests if you have nice patches that you would like to share with others.


About Windows support
*********************

``prompt_toolkit`` is cross platform, and everything that you build on top
should run fine on both Unix and Windows systems. On Windows, it uses a
different event loop (``WaitForMultipleObjects`` instead of ``select``), and
another input and output system. (Win32 APIs instead of pseudo-terminals and
VT100.)

That should work fine, however the library is currently much more tested on
Linux and Mac OS X systems. So, if you find any bugs in the Windows
implementation, or you have an idea how to make the experience better, please
create a Github issue.

It's worth noting that the implementation is a "best effort of what is
possible". Both Unix and Windows terminals have their limitations. But in
general, the Unix experience will still be a little better.


Installation
************

::

    pip install prompt-toolkit


Getting started
***************

The most simple example of the library would look like this:

.. code:: python

    from prompt_toolkit.shortcuts import get_input

    if __name__ == '__main__':
        answer = get_input('Give me some input: ')
        print('You said: %s' % answer)

For more complex examples, have a look in the ``examples`` directory. All
examples are chosen to demonstrate only one thing. Also, don't be afraid to
look at the source code. The implementation of the ``get_input`` function could
be a good start.


Projects using prompt-toolkit
*****************************

- `ptpython <http://github.com/jonathanslenders/ptpython/>`_: Python REPL
- `ptpdb <http://github.com/jonathanslenders/ptpdb/>`_: Python debugger (pdb replacement)
- `pgcli <http://pgcli.com/>`_: Postgres Shell
- `pyvim <http://github.com/jonathanslenders/pyvim/>`_: A Vim clone in pure Python

(Want your own project to be listed here? Please create a GitHub issue.)


Philosophy
**********

The source code of ``prompt_toolkit`` should be readable, concise and
efficient. We prefer short functions focussing each on one task and for which
the input and output types are clearly specified. We mostly prefer composition
over inheritance, because inheritance can result in too much functionality in
the same object. We prefer immutable objects where possible (objects don't
change after initialisation). Reusability is important. We absolutely refrain
from having a changing global state, it should be possible to have multiple
independent instances of the same code in the same process. The architecture
should be layered: the lower levels operate on primitive operations and data
structures giving -- when correctly combined -- all the possible flexibility;
while at the higher level, there should be a simpler API, ready-to-use and
sufficient for most use cases. Thinking about algorithms and efficiency is
important, but avoid premature optimization.


Special thanks to
*****************

- `Pygments <http://pygments.org/>`_: Syntax highlighter.
- `wcwidth <https://github.com/jquast/wcwidth>`_: Determine columns needed for a wide characters.

.. |Build Status| image:: https://api.travis-ci.org/jonathanslenders/python-prompt-toolkit.svg?branch=master
    :target: https://travis-ci.org/jonathanslenders/python-prompt-toolkit#

.. |PyPI| image:: https://pypip.in/version/prompt-toolkit/badge.svg
    :target: https://pypi.python.org/pypi/prompt-toolkit/
    :alt: Latest Version
