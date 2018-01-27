.. _key_bindings:

More about key bindings
-----------------------

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

Key bindings can even consist of a sequence of multiple keys. The binding is
only triggered when all the keys in this sequence are pressed.

.. code:: python

    @bindings.add('a', 'b')
    def _(event):
        " Do something if 'a' is pressed and then 'b' is pressed. "
        ...

If the user presses only `a`, then nothing will happen until either a second
key (like `b`) has been pressed or until the timeout expires (see later).


Wildcards
^^^^^^^^^

Sometimes you want to catch any key that follows after a certain key stroke.
This is possible by binding the '<any>' key:

.. code:: python

    @bindings.add('a', '<any>')
    def _(event):
        ...

This will handle `aa`, `ab`, `ac`, etcetera. The key binding can check the
`event` object for which keys exactly have been pressed.


Attaching a filter (condition)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^

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
^^^^^

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
^^^^^^^^

There are two timeout settings that effect the handling of keys.

- ``Application.input_timeout``: Like Vim's `ttimeoutlen` option.
  When to flush the input (For flushing escape keys.) This is important on
  terminals that use vt100 input. We can't distinguish the escape key from for
  instance the left-arrow key, if we don't know what follows after "\x1b". This
  little timer will consider "\x1b" to be escape if nothing did follow in this
  time span.  This seems to work like the `ttimeoutlen` option in Vim.

- ``KeyProcessor.timeout``: like Vim's `timeoutlen` option.
  This can be `None` or a float.  For instance, suppose that we have a key
  binding AB and a second key binding A. If the uses presses A and then waits,
  we don't handle this binding yet (unless it was marked 'eager'), because we
  don't know what will follow. This timeout is the maximum amount of time that
  we wait until we call the handlers anyway. Pass `None` to disable this
  timeout.
