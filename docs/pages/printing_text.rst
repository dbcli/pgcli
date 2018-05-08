.. _printing_text:

Printing (and using) formatted text
===================================

Prompt_toolkit ships with a
:func:`~prompt_toolkit.shortcuts.print_formatted_text` function that's meant to
be (as much as possible) compatible with the built-in print function, but on
top of that, also supports colors and formatting.

On Linux systems, this will output VT100 escape sequences, while on Windows it
will use Win32 API calls or VT100 sequences, depending on what is available.

.. note::

        This page is also useful if you'd like to learn how to use formatting
        in other places, like in a prompt or a toolbar. Just like
        :func:`~prompt_toolkit.shortcuts.print_formatted_text` takes any kind
        of "formatted text" as input, prompts and toolbars also accept
        "formatted text".

Printing plain text
-------------------

The print function can be imported as follows:

.. code:: python

    from __future__ import unicode_literals
    from prompt_toolkit import print_formatted_text

    print_formatted_text('Hello world')

.. note::

    `prompt_toolkit` expects unicode strings everywhere. If you are using
    Python 2, make sure that all strings which are passed to `prompt_toolkit`
    are unicode strings (and not bytes). Either use
    ``from __future__ import unicode_literals`` or explicitly put a small
    ``'u'`` in front of every string.

You can replace the built in ``print`` function as follows, if you want to.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print_formatted_text as print

    print('Hello world')

.. note::

    If you're using Python 2, make sure to add ``from __future__ import
    print_function``. Otherwise, it will not be possible to import a function
    named ``print``.

.. _formatted_text:

Formatted text
--------------

There are several ways to print colors:

- By creating an :class:`~prompt_toolkit.formatted_text.HTML` object.
- By creating an :class:`~prompt_toolkit.formatted_text.ANSI` object that
  contains ANSI escape sequences.
- By creating a list of ``(style, text)`` tuples.
- By creating a list of ``(pygments.Token, text)`` tuples, and wrapping it in
  :class:`~prompt_toolkit.formatted_text.PygmentsTokens`.

An instance of any of these three kinds of objects is called "formatted text".
There are various places in prompt toolkit, where we accept not just plain text
(as a strings), but also formatted text.

HTML
^^^^

:class:`~prompt_toolkit.formatted_text.HTML` can be used to indicate that a
string contains HTML-like formatting. It supports the basic tags for bold,
italic and underline: ``<b>``, ``<i>`` and ``<u>``.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print_formatted_text, HTML

    print = print_formatted_text

    print(HTML('<b>This is bold</b>'))
    print(HTML('<i>This is italic</b>'))
    print(HTML('<u>This is underlined</u>'))

Further, it's possible to use tags for foreground colors:

.. code:: python

    print = print_formatted_text

    # Colors from the ANSI palette.
    print(HTML('<ansired>This is red</ansired>'))
    print(HTML('<ansigreen>This is green</ansigreen>'))

    # Named colors (256 color palette, or true color, depending on the output).
    print(HTML('<skyblue>This is light pink</skyblue>'))
    print(HTML('<seagreen>This is light pink</seagreen>'))
    print(HTML('<violet>This is light pink</violet>'))

Both foreground and background colors can also be specified setting the `fg`
and `bg` attributes of any tag:

.. code:: python

    # Colors from the ANSI palette.
    print_formatted_text(HTML('<style fg="#ff0044" bg="seagreen">Red on green</style>'))

Underneath, all tags are mapped to classes from the style sheet. So, if you use
a custom tag, then you can assign a style in the stylesheet.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print_formatted_text, HTML
    from prompt_toolkit.styles import Style

    style = Style.from_dict({
        'aaa': '#ff0066',
        'bbb': '#44ff00 italic',
    })

    print_formatted_text(HTML('<aaa>Hello</aaa> <bbb>world</bbb>!'), style=style)


ANSI
^^^^

Some people like to use the VT100 ANSI escape sequences to generate output.
Natively, this is however only supported on VT100 terminals, but prompt_toolkit
can parse these, and map them to formatted text instances. This means that they
will work on Windows as well. The :class:`~prompt_toolkit.formatted.ANSI` class
takes care of that.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print_formatted_text, ANSI

    print_formatted_text(ANSI('\x1b[31mhello \x1b[32mworld'))

Keep in mind that even on a Linux VT100 terminal, the final output produced by
prompt_toolkit, is not necessarily exactly the same. Depending on the color
depth, it is possible that colors are mapped to different colors, and unknown
tags will be removed.


Style/text tuples
^^^^^^^^^^^^^^^^^

Internally, both :class:`~prompt_toolkit.formatted_text.HTML` and
:class:`~prompt_toolkit.formatted_text.ANSI` objects are mapped to a list of
``(style, text)`` tuples. It is however also possible to create such a list
manually. This is a little more verbose, but it's probably the most powerful
way of expressing formatted text.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print_formatted_text
    from prompt_toolkit.formatted_text import FormattedText

    text = FormattedText([
        ('#ff0066', 'Hello'),
        ('', ' '),
        ('#44ff00 italic', 'World'),
    ])

    print_formatted_text(text)

Similar to the :class:`~prompt_toolkit.formatted_text.HTML` example, it is also
possible to use class names, and separate the styling in a style sheet.

.. code:: python

    from __future__ import unicode_literals, print_function
    from prompt_toolkit import print_formatted_text
    from prompt_toolkit.formatted_text import FormattedText
    from prompt_toolkit.styles import Style

    # The text.
    text = FormattedText([
        ('class:aaa', 'Hello'),
        ('', ' '),
        ('class:bbb', 'World'),
    ])

    # The style sheet.
    style = Style.from_dict({
        'aaa': '#ff0066',
        'bbb': '#44ff00 italic',
    })

    print_formatted_text(text, style=style)


Pygments ``(Token, text)`` tuples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you have a list of `Pygments <http://pygments.org/>`_ ``(Token, text)``
tuples, then these can be printed by wrapping them in a
:class:`~prompt_toolkit.formatted_text.PygmentsTokens` object.

.. code:: python

    from pygments.token import Token
    from prompt_toolkit import print_formatted_text
    from prompt_toolkit.formatted_text import PygmentsTokens

    text = [
        (Token.Keyword, 'print'),
        (Token.Punctuation, '('),
        (Token.Literal.String.Double, '"'),
        (Token.Literal.String.Double, 'hello'),
        (Token.Literal.String.Double, '"'),
        (Token.Punctuation, ')'),
        (Token.Text, '\n'),
    ]

    print_formatted_text(PygmentsTokens(text))


Similarly, it is also possible to print the output of a Pygments lexer:

.. code:: python

    import pygments
    from pygments.token import Token
    from pygments.lexers import PythonLexer

    from prompt_toolkit.formatted_text import PygmentsTokens
    from prompt_toolkit import print_formatted_text

    # Printing the output of a pygments lexer.
    tokens = list(pygments.lex('print("Hello")', lexer=PythonLexer()))
    print_formatted_text(PygmentsTokens(tokens))

Prompt_toolkit ships with a default colorscheme which styles it just like
Pygments would do, but if you'd like to change the colors, keep in mind that
Pygments tokens map to classnames like this:

+-----------------------------------+---------------------------------------------+
| pygments.Token                    | prompt_toolkit classname                    |
+===================================+=============================================+
| - ``Token.Keyword``               | - ``"class:pygments.keyword"``              |
| - ``Token.Punctuation``           | - ``"class:pygments.punctuation"``          |
| - ``Token.Literal.String.Double`` | - ``"class:pygments.literal.string.double"``|
| - ``Token.Text``                  | - ``"class:pygments.text"``                 |
| - ``Token``                       | - ``"class:pygments"``                      |
+-----------------------------------+---------------------------------------------+

A classname like ``pygments.literal.string.double`` is actually decomposed in
the following four classnames: ``pygments``, ``pygments.literal``,
``pygments.literal.string`` and ``pygments.literal.string.double``. The final
style is computed by combining the style for these four classnames. So,
changing the style from these Pygments tokens can be done as follows:

.. code:: python

    from prompt_toolkit.styles import Style

    style = Style.from_dict({
        'pygments.keyword': 'underline',
        'pygments.literal.string': 'bg:#00ff00 #ffffff',
    })
    print_formatted_text(PygmentsTokens(tokens), style=style)


to_formatted_text
^^^^^^^^^^^^^^^^^

A useful function to know about is
:func:`~prompt_toolkit.formatted_text.to_formatted_text`. This ensures that the
given input is valid formatted text. While doing so, an additional style can be
applied as well.

.. code:: python

    from prompt_toolkit.formatted_text import to_formatted_text, HTML
    from prompt_toolkit import print_formatted_text

    html = HTML('<aaa>Hello</aaa> <bbb>world</bbb>!')
    text = to_formatted_text(html, style='class:my_html bg:#00ff00 italic')

    print_formatted_text(text)
