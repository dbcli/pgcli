Architecture
============


::

    +---------------------------------------------------------------+
    |     InputStream                                               |
    |     ===========                                               |
    |          - Parses the input stream coming from a VT100        |
    |            compatible terminal. Translates it into data input |
    |            and control characters. Calls the corresponding    |
    |            handlers of the `InputStreamHandel` instance.      |
    |                                                               |
    |          e.g. Translate '\x1b[6~' into "page_down", call the  |
    |               `page_down` function of `InputStreamHandler`    |
    +---------------------------------------------------------------+
               |
               v
    +---------------------------------------------------------------+
    |     InputStreamHandler                                        |
    |     ==================                                        |
    |          - Implements keybindings for control keys, arrow     |
    |            movement, escape, etc... There are two classes     |
    |            inheriting from this, which implement more         |
    |            specific key bindings.                             |
    |                  * `EmacsInputStreamHandler`                  |
    |                  * `ViInputStreamHandler`                     |
    |            Keybindings are implemented as operations of the   |
    |            `Line` object.                                     |
    |                                                               |
    |          e.g. 'ctrl_t' calls the                              |
    |               `swap_characters_before_cursor` method of       |
    |               the `Line` object.                              |
    +---------------------------------------------------------------+
               |
               v
    +---------------------------------------------------------------+
    |     Line                                                      |
    |     ====                                                      |
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
    |            | `Line` class. This is a wrapper around the    |  |
    |            | text and cursor position, and contains        |  |
    |            | methods for querying this data , e.g. to give |  |
    |            | the text before the cursor.                   |  |
    |            +-----------------------------------------------+  |
    +---------------------------------------------------------------+
        |
        |  `Line` creates a `RenderContext` instance which holds the
        |  information to visualise the command line. This is passed
        |  to the `Renderer` object. (Passing this object happens at
        |  various places.)
        |
        |     +---------------+     +-------------------------------+
        |     | RenderContext |     | Prompt                        |
        |     | ============= | --> | ======                        |
        |     |               |     |  - Responsible for the        |
        |     |               |     |    "prompt" (The leading text |
        |     |               |     |    before the actual input.)  |
        |     |               |     |                               |
        |     |               |     |    Further it actually also   |
        |     |               |     |    implements the trailing    |
        |     |               |     |    text, which could be a     |
        |     |               |     |    context sentsitive help    |
        |     |               |     |    text.                      |
        |     |               |     +-------------------------------+
        |     |               |
        |     |               |     +-------------------------------+
        |     |               | ->  | Code                          |
        |     |               |     | ====                          |
        |     |               |     |  - Implements the semantics   |
        |     |               |     |    of the command line. This  |
        |     |               |     |    are two major things:      |
        |     |               |     |                               |
        |     |               |     |      * tokenizing the input   |
        |     |               |     |        for highlighting.      |
        |     |               |     |      * Autocompletion         |
        |     +---------------+     +-------------------------------+
        |
        |  The methods from `Prompt` and `Code` which are meant for
        |  the renderer return a list of (Token, text) tuples, where
        |  `Token` is a Pygments token.
        v
    +---------------------------------------------------------------+
    |     Renderer                                                  |
    |     ========                                                  |
    |          - Responsible for painting the (Token, text) tuples  |
    |            to the terminal output.                            |
    +---------------------------------------------------------------+


