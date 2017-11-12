.. _building_prompts:

Dialogs
=======

Prompt_toolkit ships with a high level API for displaying dialogs.


Message box
-----------

.. code:: python

    from prompt_toolkit.shortcuts.dialogs import message_dialog

    message_dialog(
        title='Example dialog window',
        text='Do you want to continue?\nPress ENTER to quit.')

.. image:: ../images/dialogs/messagebox.png


Input box
---------

.. code:: python

    from prompt_toolkit.shortcuts.dialogs import input_dialog

    text = input_dialog(
        title='Input dialog example',
        text='Please type your name:')

.. image:: ../images/dialogs/inputbox.png


The ``password=True`` option can be passed to the ``input_dialog`` function to
turn this into a password input box.


Yes/No confirmation dialog
--------------------------

.. code:: python

    from prompt_toolkit.shortcuts.dialogs import yes_no_dialog

    result = yes_no_dialog(
        title='Yes/No dialog example',
        text='Do you want to confirm?')

.. image:: ../images/dialogs/confirm.png


Styling of dialogs
------------------

A custom ``Style`` instance can be passed to all dialogs to override the
default style. Also, text can be styled by passing an ``HTML`` object.


.. code:: python

    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.shortcuts.dialogs import message_dialog
    from prompt_toolkit.styles import Style

    example_style = Style.from_dict({
        'dialog':             'bg:#88ff88',
        'dialog frame-label': 'bg:#ffffff #000000',
        'dialog.body':        'bg:#000000 #00ff00',
        'dialog.body shadow': 'bg:#00aa00',
    })

    message_dialog(
        title=HTML('<style bg="blue" fg="white">Styled</style> '
                   '<style fg="ansired">dialog</style> window'),
        text='Do you want to continue?\nPress ENTER to quit.',
        style=example_style)

.. image:: ../images/dialogs/styled.png

