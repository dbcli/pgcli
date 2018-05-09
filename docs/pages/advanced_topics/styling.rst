.. _styling:

More about styling
------------------

This page will attempt to explain in more detail how to use styling in
prompt_toolkit.

To some extent, it is very similar to how `Pygments <http://pygments.org/>`_
styling works.


Style strings
^^^^^^^^^^^^^

Many user interface controls, like :class:`~prompt_toolkit.layout.Window`
accept a ``style`` argument which can be used to pass the formatting as a
string. For instance, we can select a foreground color:

- ``"fg:ansired"``  (ANSI color palette)
- ``"fg:ansiblue"`` (ANSI color palette)
- ``"fg:#ffaa33"``  (hexadecimal notation)
- ``"fg:darkred"``  (named color)

Or a background color:

- ``"bg:ansired"``  (ANSI color palette)
- ``"bg:#ffaa33"``  (hexadecimal notation)

Or we can add one of the following flags:

- ``"bold"``
- ``"italic"``
- ``"underline"``
- ``"blink"``
- ``"reverse"``  (reverse foreground and background on the terminal.)
- ``"hidden"``

Or their negative variants:

- ``"nobold"``
- ``"noitalic"``
- ``"nounderline"``
- ``"noblink"``
- ``"noreverse"``
- ``"nohidden"``

All of these formatting options can be combined as well:

- ``"fg:ansiyellow bg:black bold underline"``

The style string can be given to any user control directly, or to a
:class:`~prompt_toolkit.layout.Container` object from where it will propagate
to all its children. A style defined by a parent user control can be overridden
by any of its children. The parent can for instance say ``style="bold
underline"`` where a child overrides this style partly by specifying
``style="nobold bg:ansired"``.

.. note::

    These styles are actually compatible with
    `Pygments <http://pygments.org/>`_ styles, with additional support for
    `reverse` and `blink`. Further, we ignore flags like `roman`, `sans`,
    `mono` and `border`.

The following ANSI colors are available (both for foreground and background):

.. code::

    # Low intensity, dark.  (One or two components 0x80, the other 0x00.)
    ansiblack, ansired, ansigreen, ansiyellow, ansiblue
    ansimagenta, 'ansicyan, ansigray

    # High intensity, bright.
    ansibrightblack, ansibrightred, ansibrightgreen, ansibrightyellow
    ansibrightblue, ansibrightmagenta, ansibrightcyan, ansiwhite

In order to know which styles are actually used in an application, it is
possible to call :meth:`~Application.get_used_style_strings`, when the
application is done.


Class names
^^^^^^^^^^^

Like we do for web design, it is not a good habit to specify all styling
inline. Instead, we can attach class names to UI controls and have a style
sheet that refers to these class names. The
:class:`~prompt_toolkit.style.Style` can be passed as an argument to the
:class:`~prompt_toolkit.application.Application`.

.. code:: python

    from prompt_toolkit.layout import VSplit, Window
    from prompt_toolkit.style import Style

    layout = VSplit([
        Window(BufferControl(...), style='class:left'),
        HSplit([
            Window(BufferControl(...), style='class:top'),
            Window(BufferControl(...), style='class:bottom'),
        ], style='class:right')
    ])

    style = Style([
         ('left': 'bg:ansired'),
         ('top': 'fg:#00aaaa'),
         ('bottom': 'underline bold'),
     ])

It is possible to add multiple class names to an element. That way we'll
combine the styling for these class names. Multiple classes can be passed by
using a comma separated list, or by using the ``class:`` prefix twice.

.. code:: python

   Window(BufferControl(...), style='class:left,bottom'),
   Window(BufferControl(...), style='class:left class:bottom'),

It is possible to combine class names and inline styling. The order in which
the class names and inline styling is specified determines the order of
priority. In the following example for instance, we'll take first the style of
the "header" class, and then override that with a red background color.

.. code:: python

    Window(BufferControl(...), style='class:header bg:red'),


Dot notation in class names
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The dot operator has a special meaning in a class name. If we write:
``style="class:a.b.c"``, then this will actually expand to the following:
``style="class:a class:a.b class:a.b.c"``.

This is mainly added for `Pygments <http://pygments.org/>`_ lexers, which
specify "Tokens" like this, but it's useful in other situations as well.


Multiple classes in a style sheet
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A style sheet can be more complex as well. We can for instance specify two
class names. The following will underline the left part within the header, or
whatever has both the class "left" and the class "header" (the order doesn't
matter).

.. code:: python

    style = Style([
         ('header left': 'underline'),
     ])


If you have a dotted class, then it's required to specify the whole path in the
style sheet (just typing ``c`` or ``b.c`` doesn't work if the class is
``a.b.c``):

.. code:: python

    style = Style([
         ('a.b.c': 'underline'),
     ])

It is possible to combine this:

.. code:: python

    style = Style([
         ('header body left.text': 'underline'),
     ])


Evaluation order of rules in a style sheet
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The style is determined as follows:

- First, we concatenate all the style strings from the root control through all
  the parents to the child in one big string. (Things at the right take
  precedence anyway.)

  E.g: ``class:body bg:#aaaaaa #000000 class:header.focused class:left.text.highlighted underline``

- Then we go through this style from left to right, starting from the default
  style. Inline styling is applied directly.
  
  If we come across a class name, then we generate all combinations of the
  class names that we collected so far (this one and all class names to the
  left), and for each combination which includes the new class name, we look
  for matching rules in our style sheet.  All these rules are then applied
  (later rules have higher priority).

  If we find a dotted class name, this will be expanded in the individual names
  (like ``class:left class:left.text class:left.text.highlighted``), and all
  these are applied like any class names.

- Then this final style is applied to this user interface element.


Using a dictionary as a style sheet
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The order of the rules in a style sheet is meaningful, so typically, we use a
list of tuples to specify the style. But is also possible to use a dictionary
as a style sheet. This makes sense for Python 3.6, where dictionaries remember
their ordering. An ``OrderedDict`` works as well.

.. code:: python

    from prompt_toolkit.style import Style

    style = Style.from_dict({
         'header body left.text': 'underline',
    })


Loading a style from Pygments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


`Pygments <http://pygments.org/>`_ has a slightly different notation for
specifying styles, because it maps styling to Pygments "Tokens". A Pygments
style can however be loaded and used as follows:

.. code:: python

    from prompt_toolkit.styles.from_pygments import style_from_pygments_cls
    from pygments.styles import get_style_by_name

    style = style_from_pygments_cls(get_style_by_name('monokai'))


Merging styles together
^^^^^^^^^^^^^^^^^^^^^^^

Multiple :class:`~prompt_toolkit.style.Style` objects can be merged together as
follows:

.. code:: python

    from prompt_toolkit.styles import merge_styles

    style = merge_styles([
        style1,
        style2,
        style3
    ])


Color depths
^^^^^^^^^^^^

There are four different levels of color depths available:

+--------+-----------------+-----------------------------+---------------------------------+
| 1 bit  | Black and white | ``ColorDepth.DEPTH_1_BIT``  | ``ColorDepth.MONOCHROME``       |
+--------+-----------------+-----------------------------+---------------------------------+
| 4 bit  | ANSI colors     | ``ColorDepth.DEPTH_4_BIT``  | ``ColorDepth.ANSI_COLORS_ONLY`` |
+--------+-----------------+-----------------------------+---------------------------------+
| 8 bit  | 256 colors      | ``ColorDepth.DEPTH_8_BIT``  | ``ColorDepth.DEFAULT``          |
+--------+-----------------+-----------------------------+---------------------------------+
| 24 bit | True colors     | ``ColorDepth.DEPTH_24_BIT`` | ``ColorDepth.TRUE_COLOR``       |
+--------+-----------------+-----------------------------+---------------------------------+

By default, 256 colors are used, because this is what most terminals support
these days. If the ``TERM`` enviroment variable is set to ``linux`` or
``eterm-color``, then only ANSI colors are used, because of these terminals. 24
bit true color output needs to be enabled explicitely. When 4 bit color output
is chosen, all colors will be mapped to the closest ANSI color.

Setting the default color depth for any prompt_toolkit application can be done
by setting the ``PROMPT_TOOLKIT_COLOR_DEPTH`` environment variable. You could
for instance copy the following into your `.bashrc` file.

.. code:: shell

    # export PROMPT_TOOLKIT_COLOR_DEPTH=DEPTH_1_BIT
    export PROMPT_TOOLKIT_COLOR_DEPTH=DEPTH_4_BIT
    # export PROMPT_TOOLKIT_COLOR_DEPTH=DEPTH_8_BIT
    # export PROMPT_TOOLKIT_COLOR_DEPTH=DEPTH_24_BIT

An application can also decide to set the color depth manually by passing a
:class:`~prompt_toolkit.output.ColorDepth` value to the
:class:`~prompt_toolkit.application.Application` object:

.. code:: python

    from prompt_toolkit.output.color_depth import ColorDepth

    app = Application(
        color_depth=ColorDepth.ANSI_COLORS_ONLY,
        # ...
    )
