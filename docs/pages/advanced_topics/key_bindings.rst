.. _key_bindings:

Move about key bindings
=======================

This page contains a few additional notes about key bindings.


Key bindings can be defined as follows by creating a
:class:`~prompt_toolkit.key_binding.KeyBindings` instance:


.. code:: python

    from prompt_toolkit.key_binding import KeyBindings

    bindings = KeyBindings()

    @bindings.add('a')
    def _(event):
        " Do something if 'a' has been pressed. "
        ...


    @bindings.add('c-t')
    def _(event):
        " Do something if Control-T has been pressed. "
        ...

.. note::

    :kbd:`c-q` (control-q) and :kbd:`c-s` (control-s) are often captured by the
    terminal, because they were used traditionally for software flow control.
    When this is enabled, the application will automatically freeze when
    :kbd:`c-s` is pressed, until :kbd:`c-q` is pressed. It won't be possible to
    bind these keys.

    In order to disable this, execute type the following in your shell, or even
    add it to your `.bashrc`.

    .. code::

        stty -ixon

Key bindings can even consist of a sequence of multiple keys. The binding is
only triggered when all the keys in this sequence are pressed.

.. code:: python

    @bindings.add('a', 'b')
    def _(event):
        " Do something if 'a' is pressed and then 'b' is pressed. "
        ...

If the user presses only `a`, then nothing will happen until either a second
key (like `b`) has been pressed or until the timeout expires (see later).


List of special keys
--------------------

Besides literal characters, any of the following keys can be used in a key
binding:

+-------------------+-----------------------------------------+
| Name              + Possible keys                           |
+===================+=========================================+
| Escape            | :kbd:`escape`                           |
+-------------------+-----------------------------------------+
| Arrows            | :kbd:`left`,                            |
|                   | :kbd:`right`,                           |
|                   | :kbd:`up`,                              |
|                   | :kbd:`down`                             |
+-------------------+-----------------------------------------+
| Navigation        | :kbd:`home`,                            |
|                   | :kbd:`end`,                             |
|                   | :kbd:`delete`,                          |
|                   | :kbd:`pageup`,                          |
|                   | :kbd:`pagedown`,                        |
|                   | :kbd:`insert`                           |
+-------------------+-----------------------------------------+
| Control+lowercase | :kbd:`c-a`, :kbd:`c-b`, :kbd:`c-c`,     |
|                   | :kbd:`c-d`, :kbd:`c-e`, :kbd:`c-f`,     |
|                   | :kbd:`c-g`, :kbd:`c-h`, :kbd:`c-i`,     |
|                   | :kbd:`c-j`, :kbd:`c-k`, :kbd:`c-l`,     |
|                   |                                         |
|                   | :kbd:`c-m`, :kbd:`c-n`, :kbd:`c-o`,     |
|                   | :kbd:`c-p`, :kbd:`c-q`, :kbd:`c-r`,     |
|                   | :kbd:`c-s`, :kbd:`c-t`, :kbd:`c-u`,     |
|                   | :kbd:`c-v`, :kbd:`c-w`, :kbd:`c-x`,     |
|                   |                                         |
|                   | :kbd:`c-y`, :kbd:`c-z`                  |
+-------------------+-----------------------------------------+
| Control+uppercase | :kbd:`c-A`, :kbd:`c-B`, :kbd:`c-C`,     |
|                   | :kbd:`c-D`, :kbd:`c-E`, :kbd:`c-F`,     |
|                   | :kbd:`c-G`, :kbd:`c-H`, :kbd:`c-I`,     |
|                   | :kbd:`c-J`, :kbd:`c-K`, :kbd:`c-L`,     |
|                   |                                         |
|                   | :kbd:`c-M`, :kbd:`c-N`, :kbd:`c-O`,     |
|                   | :kbd:`c-P`, :kbd:`c-Q`, :kbd:`c-R`,     |
|                   | :kbd:`c-S`, :kbd:`c-T`, :kbd:`c-U`,     |
|                   | :kbd:`c-V`, :kbd:`c-W`, :kbd:`c-X`,     |
|                   |                                         |
|                   | :kbd:`c-Y`, :kbd:`c-Z`                  |
+-------------------+-----------------------------------------+
| Control + arrow   | :kbd:`c-left`,                          |
|                   | :kbd:`c-right`,                         |
|                   | :kbd:`c-up`,                            |
|                   | :kbd:`c-down`                           |
+-------------------+-----------------------------------------+
| Other control     | :kbd:`c-@`,                             |
| keys              | :kbd:`c-\\`,                            |
|                   | :kbd:`c-]`,                             |
|                   | :kbd:`c-^`,                             |
|                   | :kbd:`c-_`,                             |
|                   | :kbd:`c-delete`                         |
+-------------------+-----------------------------------------+
| Shift + arrow     | :kbd:`s-left`,                          |
|                   | :kbd:`s-right`,                         |
|                   | :kbd:`s-up`,                            |
|                   | :kbd:`s-down`                           |
+-------------------+-----------------------------------------+
| Other shift       | :kbd:`s-delete`,                        |
| keys              | :kbd:`s-tab`                            |
+-------------------+-----------------------------------------+
| F-keys            | :kbd:`f1`, :kbd:`f2`, :kbd:`f3`,        |
|                   | :kbd:`f4`, :kbd:`f5`, :kbd:`f6`,        |
|                   | :kbd:`f7`, :kbd:`f8`, :kbd:`f9`,        |
|                   | :kbd:`f10`, :kbd:`f11`, :kbd:`f12`,     |
|                   |                                         |
|                   | :kbd:`f13`, :kbd:`f14`, :kbd:`f15`,     |
|                   | :kbd:`f16`, :kbd:`f17`, :kbd:`f18`,     |
|                   | :kbd:`f19`, :kbd:`f20`, :kbd:`f21`,     |
|                   | :kbd:`f22`, :kbd:`f23`, :kbd:`f24`      |
+-------------------+-----------------------------------------+

There are a couple of useful aliases as well:

+-------------------+-------------------+
| :kbd:`c-h`        | :kbd:`backspace`  |
+-------------------+-------------------+
| :kbd:`c-@`        | :kbd:`c-space`    |
+-------------------+-------------------+
| :kbd:`c-m`        | :kbd:`enter`      |
+-------------------+-------------------+
| :kbd:`c-i`        | :kbd:`tab`        |
+-------------------+-------------------+

.. note::

    Note that the supported keys are limited to what typical VT100 terminals
    offer. Binding :kbd:`c-7` (control + number 7) for instance is not
    supported.


Binding alt+something, option+something or meta+something
---------------------------------------------------------

Vt100 terminals translate the alt key into a leading :kbd:`escape` key.
For instance, in order to handle :kbd:`alt-f`, we have to handle
:kbd:`escape` + :kbd:`f`. Notice that we receive this as two individual keys.
This means that it's exactly the same as first typing :kbd:`escape` and then
typing :kbd:`f`. Something this alt-key is also known as option or meta.

In code that looks as follows:

.. code:: python

    @bindings.add('escape', 'f')
    def _(event):
        " Do something if alt-f or meta-f have been pressed. "


Wildcards
---------

Sometimes you want to catch any key that follows after a certain key stroke.
This is possible by binding the '<any>' key:

.. code:: python

    @bindings.add('a', '<any>')
    def _(event):
        ...

This will handle `aa`, `ab`, `ac`, etcetera. The key binding can check the
`event` object for which keys exactly have been pressed.


Attaching a filter (condition)
------------------------------

In order to enable a key binding according to a certain condition, we have to
pass it a :class:`~prompt_toolkit.filters.Filter`, usually a
:class:`~prompt_toolkit.filters.Condition` instance. (:ref:`Read more about
filters <filters>`.)

.. code:: python

    from prompt_toolkit.filters import Condition

    @Condition
    def is_active():
        " Only activate key binding on the second half of each minute. "
        return datetime.datetime.now().second > 30

    @bindings.add('c-t', filter=is_active)
    def _(event):
        # ...
        pass

The key binding will be ignored when this condition is not satisfied.


ConditionalKeyBindings: Disabling a set of key bindings
-------------------------------------------------------

Sometimes you want to enable or disable a whole set of key bindings according
to a certain condition. This is possible by wrapping it in a
:class:`~prompt_toolkit.key_binding.ConditionalKeyBindings` object.

.. code:: python

    from prompt_toolkit.key_binding import ConditionalKeyBindings

    @Condition
    def is_active():
        " Only activate key binding on the second half of each minute. "
        return datetime.datetime.now().second > 30

     bindings = ConditionalKeyBindings(
         key_bindings=my_bindings,
         filter=is_active)

If the condition is not satisfied, all the key bindings in `my_bindings` above
will be ignored.


Merging key bindings
--------------------

Sometimes you have different parts of your application generate a collection of
key bindings. It is possible to merge them together through the
:func:`~prompt_toolkit.key_binding.merge_key_bindings` function. This is
preferred above passing a :class:`~prompt_toolkit.key_binding.KeyBindings`
object around and having everyone populate it.

.. code:: python

    from prompt_toolkit.key_binding import merge_key_bindings

    bindings = merge_key_bindings([
        bindings1,
        bindings2,
    ])


Eager
-----

Usually not required, but if ever you have to override an existing key binding,
the `eager` flag can be useful.

Suppose that there is already an active binding for `ab` and you'd like to add
a second binding that only handles `a`. When the user presses only `a`,
prompt_toolkit has to wait for the next key press in order to know which
handler to call.

By passing the `eager` flag to this second binding, we are actually saying that
prompt_toolkit shouldn't wait for longer matches when all the keys in this key
binding are matched. So, if `a` has been pressed, this second binding will be
called, even if there's an active `ab` binding.

.. code:: python

    @bindings.add('a', 'b')
    def binding_1(event):
        ...

    @bindings.add('a', eager=True)
    def binding_2(event):
        ...

This is mainly useful in order to conditionally override another binding.


Timeouts
--------

There are two timeout settings that effect the handling of keys.

- ``Application.ttimeoutlen``: Like Vim's `ttimeoutlen` option.
  When to flush the input (For flushing escape keys.) This is important on
  terminals that use vt100 input. We can't distinguish the escape key from for
  instance the left-arrow key, if we don't know what follows after "\x1b". This
  little timer will consider "\x1b" to be escape if nothing did follow in this
  time span.  This seems to work like the `ttimeoutlen` option in Vim.

- ``KeyProcessor.timeoutlen``: like Vim's `timeoutlen` option.
  This can be `None` or a float.  For instance, suppose that we have a key
  binding AB and a second key binding A. If the uses presses A and then waits,
  we don't handle this binding yet (unless it was marked 'eager'), because we
  don't know what will follow. This timeout is the maximum amount of time that
  we wait until we call the handlers anyway. Pass `None` to disable this
  timeout.


Recording macros
----------------

Both Emacs and Vi mode allow macro recording. By default, all key presses are
recorded during a macro, but it is possible to exclude certain keys by setting
the `record_in_macro` parameter to `False`:

.. code:: python

    @bindings.add('c-t', record_in_macro=False)
    def _(event):
        # ...
        pass


Processing `.inputrc`
---------------------

GNU readline can be configured using an `.inputrc` configuration file. This can
could key bindings as well as certain settings. Right now, prompt_toolkit
doesn't support `.inputrc` yet, but it should be possible in the future.
