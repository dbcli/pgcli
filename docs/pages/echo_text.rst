.. _echo_text:

Echoing text
============

Prompt_toolkit ships with a ``print`` function that's meant to be compatible
with the built-in print function, but on top of that, also supports colors and
formatting.

On Linux systems, this will output VT100 escape sequences, while on Windows it
will use Win32 API calls or VT100 sequences, depending on what is available.


Printing plain text
-------------------

The print function can be imported as follows:

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print

    print('Hello world')

.. warning::

    If you're using Python 2, make sure to add ``from __future__ import
    print_function``. Otherwise, it will not be possible to import a function
    named ``print``.


Colors and formatting
---------------------

There are three ways to print colors:

- By creating an HTML object.
- By creating an ANSI object that contains ANSI escape sequences.
- By creating a list of ``(style, text)`` tuples.


HTML
^^^^

``prompt_toolkit.HTML`` can be used to indicate that a string contains
HTML-like formatting. It supports the basic tags for bold, italic and
underline: ``<b>``, ``<i>`` and ``<u>``.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print, HTML

    print(HTML('<b>This is bold</b>'))
    print(HTML('<i>This is italic</b>'))
    print(HTML('<u>This is italic</u>'))

Further, it's possible to use tags for foreground colors:

.. code:: python

    # Colors from the ANSI palette.
    print(HTML('<ansired>This is red</ansired>'))
    print(HTML('<ansigreen>This is green</ansigreen>'))

    # Named colors (256 color palette, or true color, depending on the output).
    print(HTML('<skyblue>This is light pink</skyblue>'))
    print(HTML('<seagreen>This is light pink</seagreen>'))
    print(HTML('<violet>This is light pink</violet>'))

Both foreground and background colors can also be defined using the `fg` and
`bg` attributes of any tag:

.. code:: python

    # Colors from the ANSI palette.
    print(HTML('<span fg="#ff0044" bg="seegreen">Red on green</span>'))


Underneath, all tags are mapped to classes from the style sheet. So, if you use
a custom tag, then you can assign a style in the stylesheet.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print, HTML
    from prompt_toolkit.styles import Style

    style = Style.from_dict({
        'aaa': '#ff0066',
        'bbb': '#44ff00 italic',
    })

    print(HTML('<aaa>Hello</aaa> <bbb>world</bbb>!'), style=style)


ANSI
^^^^

Some people like to use the VT100 ANSI escape squences to generate output.
Natively, this is however only supported on VT100 terminals, but prompt_toolkit
can parse these, and map it to whatever terminal or console is available. This
means that it will work on Windows as well.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print, ANSI

    print(ANSI('\x1b[31mhello \x1b[32mworld'))
