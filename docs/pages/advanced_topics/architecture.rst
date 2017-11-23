.. _architecture:


Architecture
------------

TODO: this is a little outdated.

::

    +---------------------------------------------------------------+
    |     InputStream                                               |
    |     ===========                                               |
    |          - Parses the input stream coming from a VT100        |
    |            compatible terminal. Translates it into data input |
    |            and control characters. Calls the corresponding    |
    |            handlers of the `InputStreamHandler` instance.     |
    |                                                               |
    |          e.g. Translate '\x1b[6~' into "Keys.PageDown", call  |
    |               the `feed_key` method of `InputProcessor`.      |
    +---------------------------------------------------------------+
               |
               v
    +---------------------------------------------------------------+
    |     InputStreamHandler                                        |
    |     ==================                                        |
    |          - Has a `Registry` of key bindings, it calls the     |
    |            bindings according to the received keys and the    |
    |            input mode.                                        |
    |                                                               |
    |         We have Vi and Emacs bindings.
    +---------------------------------------------------------------+
               |
               v
    +---------------------------------------------------------------+
    |     Key bindings                                              |
    |     ============                                              |
    |          - Every key binding consists of a function that      |
    |            receives an `Event` and usually it operates on     |
    |            the `Buffer` object. (It could insert data or      |
    |            move the cursor for example.)                      |
    +---------------------------------------------------------------+
        |
        | Most of the key bindings operate on a `Buffer` object, but
        | they don't have to. They could also change the visibility
        | of a menu for instance, or change the color scheme.
        |
        v
    +---------------------------------------------------------------+
    |     Buffer                                                    |
    |     ======                                                    |
    |          - Contains a data structure to hold the current      |
    |            input (text and cursor position). This class       |
    |            implements all text manipulations and cursor       |
    |            movements (Like e.g. cursor_forward, insert_char   |
    |            or delete_word.)                                   |
    |                                                               |
    |            +-----------------------------------------------+  |
    |            | Document (text, cursor_position)              |  |
    |            | ================================              |  |
    |            | Accessed as the `document` property of the    |  |
    |            | `Buffer` class. This is a wrapper around the  |  |
    |            | text and cursor position, and contains        |  |
    |            | methods for querying this data , e.g. to give |  |
    |            | the text before the cursor.                   |  |
    |            +-----------------------------------------------+  |
    +---------------------------------------------------------------+
        |
        |  Normally after every key press, the output will be
        |  rendered again. This happens in the event loop of
        |  the `CommandLineInterface` where `Renderer.render` is
        |  called.
        v
    +---------------------------------------------------------------+
    |     Layout                                                    |
    |     ======                                                    |
    |          - When the renderer should redraw, the renderer      |
    |            asks the layout what the output should look like.  |
    |          - The layout operates on a `Screen` object that he   |
    |            received from the `Renderer` and will put the      |
    |            toolbars, menus, highlighted content and prompt    |
    |            in place.                                          |
    |                                                               |
    |            +-----------------------------------------------+  |
    |            | Menus, toolbars, prompt                       |  |
    |            | =======================                       |  |
    |            |                                               |  |
    |            +-----------------------------------------------+  |
    +---------------------------------------------------------------+
        |
        v
    +---------------------------------------------------------------+
    |     Renderer                                                  |
    |     ========                                                  |
    |          - Calculates the difference between the last output  |
    |            and the new one and writes it to the terminal      |
    |            output.                                            |
    +---------------------------------------------------------------+
