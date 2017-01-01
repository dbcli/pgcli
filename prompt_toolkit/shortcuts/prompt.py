"""
Line editing functionality.
---------------------------

This provides a UI for a line input, similar to GNU Readline, libedit and
linenoise.

Either call the `prompt` function for every line input. Or create an instance
of the :class:`.Prompt` class and call the `prompt` method from that class. In
the second case, we'll have a 'session' that keeps all the state like the
history in between several calls.

There is a lot of overlap between the arguments taken by the `prompt` function
and the `Prompt` (like `completer`, `style`, etcetera). There we have the
freedom to decide which settings we want for the whole 'session', and which we
want for an individual `prompt`.

Example::

        # Simple `prompt` call.
        result = prompt('Say something: ')

        # Using a 'session'.
        p = Prompt()
        result = p.prompt('Say something: ')
"""
from __future__ import unicode_literals

from prompt_toolkit.auto_suggest import DynamicAutoSuggest
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.clipboard import DynamicClipboard, InMemoryClipboard
from prompt_toolkit.completion import DynamicCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER, EditingMode
from prompt_toolkit.eventloop.base import EventLoop
from prompt_toolkit.eventloop.defaults import create_event_loop #, create_asyncio_event_loop
from prompt_toolkit.filters import is_done, has_focus, RendererHeightIsKnown, to_simple_filter, Condition
from prompt_toolkit.history import InMemoryHistory, DynamicHistory
from prompt_toolkit.input.defaults import create_input
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, DynamicKeyBindings, merge_key_bindings, ConditionalKeyBindings, KeyBindingsBase
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Window, HSplit, FloatContainer, Float
from prompt_toolkit.layout.containers import ConditionalContainer, Align
from prompt_toolkit.layout.controls import BufferControl, TokenListControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.lexers import DynamicLexer
from prompt_toolkit.layout.margins import PromptMargin, ConditionalMargin
from prompt_toolkit.layout.menus import CompletionsMenu, MultiColumnCompletionsMenu
from prompt_toolkit.layout.processors import Processor, DynamicProcessor, PasswordProcessor, ConditionalProcessor, AppendAutoSuggestion, HighlightSearchProcessor, HighlightSelectionProcessor, DisplayMultipleCursors, BeforeInput, ReverseSearchProcessor, ShowArg, merge_processors
from prompt_toolkit.layout.toolbars import ValidationToolbar, SystemToolbar, ArgToolbar, SearchToolbar
from prompt_toolkit.layout.utils import explode_tokens
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.styles import DEFAULT_STYLE, Style, DynamicStyle
from prompt_toolkit.token import Token
from prompt_toolkit.utils import DummyContext
from prompt_toolkit.validation import DynamicValidator

from six import text_type, exec_

import textwrap
import threading
import time
import sys

__all__ = (
    'Prompt',
    'prompt',
    'prompt_async',
    'confirm',
    'create_confirm_prompt',  # Used by '_display_completions_like_readline'.
)


def _split_multiline_prompt(get_prompt_tokens):
    """
    Take a `get_prompt_tokens` function and return three new functions instead.
    One that tells whether this prompt consists of multiple lines; one that
    returns the tokens to be shown on the lines above the input; and another
    one with the tokens to be shown at the first line of the input.
    """
    def has_before_tokens(app):
        for token, char in get_prompt_tokens(app):
            if '\n' in char:
                return True
        return False

    def before(app):
        result = []
        found_nl = False
        for token, char in reversed(explode_tokens(get_prompt_tokens(app))):
            if found_nl:
                result.insert(0, (token, char))
            elif char == '\n':
                found_nl = True
        return result

    def first_input_line(app):
        result = []
        for token, char in reversed(explode_tokens(get_prompt_tokens(app))):
            if char == '\n':
                break
            else:
                result.insert(0, (token, char))
        return result

    return has_before_tokens, before, first_input_line


class _RPrompt(Window):
    " The prompt that is displayed on the right side of the Window. "
    def __init__(self, get_tokens):
        super(_RPrompt, self).__init__(
            TokenListControl(get_tokens),
            align=Align.RIGHT)


def _true(value):
    " Test whether `value` is True. In case of a SimpleFilter, call it. "
    return to_simple_filter(value)()


class Prompt(object):
    """
    The Prompt application, which can be used as a GNU Readline replacement.

    This is a wrapper around a lot of ``prompt_toolkit`` functionality and can
    be a replacement for `raw_input`.

    :param message: Text to be shown before the prompt.
    :param multiline: `bool` or :class:`~prompt_toolkit.filters.AppFilter`.
        When True, prefer a layout that is more adapted for multiline input.
        Text after newlines is automatically indented, and search/arg input is
        shown below the input, instead of replacing the prompt.
    :param wrap_lines: `bool` or :class:`~prompt_toolkit.filters.AppFilter`.
        When True (the default), automatically wrap long lines instead of
        scrolling horizontally.
    :param is_password: Show asterisks instead of the actual typed characters.
    :param editing_mode: ``EditingMode.VI`` or ``EditingMode.EMACS``.
    :param vi_mode: `bool`, if True, Identical to ``editing_mode=EditingMode.VI``.
    :param complete_while_typing: `bool` or
        :class:`~prompt_toolkit.filters.SimpleFilter`. Enable autocompletion
        while typing.
    :param enable_history_search: `bool` or
        :class:`~prompt_toolkit.filters.SimpleFilter`. Enable up-arrow parting
        string matching.
    :param lexer: :class:`~prompt_toolkit.layout.lexers.Lexer` to be used for
        the syntax highlighting.
    :param validator: :class:`~prompt_toolkit.validation.Validator` instance
        for input validation.
    :param completer: :class:`~prompt_toolkit.completion.Completer` instance
        for input completion.
    :param reserve_space_for_menu: Space to be reserved for displaying the menu.
        (0 means that no space needs to be reserved.)
    :param auto_suggest: :class:`~prompt_toolkit.auto_suggest.AutoSuggest`
        instance for input suggestions.
    :param style: :class:`.Style` instance for the color scheme.
    :param enable_system_bindings: `bool` or
        :class:`~prompt_toolkit.filters.AppFilter`. Pressing Meta+'!' will show
        a system prompt.
    :param enable_open_in_editor: `bool` or
        :class:`~prompt_toolkit.filters.AppFilter`. Pressing 'v' in Vi mode or
        C-X C-E in emacs mode will open an external editor.
    :param history: :class:`~prompt_toolkit.history.History` instance.
    :param clipboard: :class:`~prompt_toolkit.clipboard.base.Clipboard` instance.
        (e.g. :class:`~prompt_toolkit.clipboard.in_memory.InMemoryClipboard`)
    :param get_bottom_toolbar_tokens: Optional callable which takes a
        :class:`~prompt_toolkit.application.Application` and returns a
        list of tokens for the bottom toolbar.
    :param get_continuation_tokens: An optional callable that takes a
        Application and width as input and returns a list of (Token,
        text) tuples to be used for the continuation.
    :param get_prompt_tokens: An optional callable that returns the tokens to be
        shown in the menu. (To be used instead of a `message`.)
    :param display_completions_in_columns: `bool` or
        :class:`~prompt_toolkit.filters.AppFilter`. Display the completions in
        multiple columns.
    :param get_title: Callable that returns the title to be displayed in the
        terminal.
    :param mouse_support: `bool` or :class:`~prompt_toolkit.filters.AppFilter`
        to enable mouse support.
    :param default: The default input text to be shown. (This can be edited by
        the user).
    :param patch_stdout: Replace ``sys.stdout`` by a proxy that ensures that
        print statements from other threads won't destroy the prompt. (They
        will be printed above the prompt instead.)
    :param true_color: When True, use 24bit colors instead of 256 colors.
    :param refresh_interval: (number; in seconds) When given, refresh the UI
        every so many seconds.
    """
    _fields = (
        'message', 'lexer', 'completer', 'is_password', 'editing_mode',
        'extra_key_bindings', 'include_default_key_bindings', 'is_password',
        'get_bottom_toolbar_tokens', 'style', 'get_prompt_tokens',
        'get_rprompt_tokens', 'multiline', 'get_continuation_tokens',
        'wrap_lines', 'history', 'enable_history_search',
        'complete_while_typing',
        'display_completions_in_columns', 'mouse_support', 'auto_suggest',
        'clipboard', 'get_title', 'validator', 'patch_stdout',
        'refresh_interval', 'extra_input_processor', 'default',
        'enable_system_bindings', 'enable_open_in_editor',
        'reserve_space_for_menu', 'tempfile_suffix')

    def __init__(
            self,
            message='',
            loop=None,
            default='',
            multiline=False,
            wrap_lines=True,
            is_password=False,
            vi_mode=False,
            editing_mode=EditingMode.EMACS,
            complete_while_typing=True,
            enable_history_search=False,
            lexer=None,
            enable_system_bindings=False,
            enable_open_in_editor=False,
            validator=None,
            completer=None,
            reserve_space_for_menu=8,
            auto_suggest=None,
            style=None,
            history=None,
            clipboard=None,
            get_prompt_tokens=None,
            get_continuation_tokens=None,
            get_rprompt_tokens=None,
            get_bottom_toolbar_tokens=None,
            display_completions_in_columns=False,
            get_title=None,
            mouse_support=False,
            extra_input_processor=None,
            extra_key_bindings=None,
            include_default_key_bindings=True,
            erase_when_done=False,
            tempfile_suffix='.txt',

            refresh_interval=0,
            patch_stdout=False,
            true_color=False,
            input=None,
            output=None):
        assert isinstance(message, text_type), 'Please provide a unicode string.'
        assert loop is None or isinstance(loop, EventLoop)
        assert get_bottom_toolbar_tokens is None or callable(get_bottom_toolbar_tokens)
        assert get_prompt_tokens is None or callable(get_prompt_tokens)
        assert get_rprompt_tokens is None or callable(get_rprompt_tokens)
        assert not (message and get_prompt_tokens)
        assert style is None or isinstance(style, Style)
        assert extra_input_processor is None or isinstance(extra_input_processor, Processor)
        assert extra_key_bindings is None or isinstance(extra_key_bindings, KeyBindingsBase)

        # Defaults.
        loop = loop or create_event_loop()

        output = output or create_output(true_color)
        input = input or create_input(sys.stdin)
        extra_input_processor = extra_input_processor

        history = history or InMemoryHistory()
        clipboard = clipboard or InMemoryClipboard()

        # Ensure backwards-compatibility, when `vi_mode` is passed.
        if vi_mode:
            editing_mode = EditingMode.VI

        # Store all settings in this class.
        self.loop = loop
        self.input = input
        self.output = output

        # Store all settings in this class.
        for name in self._fields:
            if name not in ('editing_mode', ):
                value = locals()[name]
                setattr(self, name, value)

        self.app, self._default_buffer, self._default_buffer_control = \
            self._create_application(editing_mode, erase_when_done)

    def _create_application(self, editing_mode, erase_when_done):
        def dyncond(attr_name):
            """
            Dynamically take this setting from this 'Prompt' class.
            `attr_name` represents an attribute name of this class. Its value
            can either be a boolean or a `SimpleFilter`.

            This returns something that can be used as either a `SimpleFilter`
            or `AppFilter`.
            """
            @Condition
            def dynamic(*a):
                value = getattr(self, attr_name)
                return to_simple_filter(value)()
            return dynamic

        # Create functions that will dynamically split the prompt. (If we have
        # a multiline prompt.)
        has_before_tokens, get_prompt_tokens_1, get_prompt_tokens_2 = \
            _split_multiline_prompt(self._get_prompt_tokens)

        # Create buffers list.
        def accept(app, buff):
            """ Accept the content of the default buffer. This is called when
            the validation succeeds. """
            app.set_return_value(buff.document.text)

            # Reset content before running again.
            app.pre_run_callables.append(buff.reset)

        default_buffer = Buffer(
            name=DEFAULT_BUFFER,
            loop=self.loop,
                # Make sure that complete_while_typing is disabled when
                # enable_history_search is enabled. (First convert to
                # SimpleFilter, to avoid doing bitwise operations on bool
                # objects.)
            complete_while_typing=Condition(lambda:
                _true(self.complete_while_typing) and not
                _true(self.enable_history_search)),
            enable_history_search=dyncond('enable_history_search'),
            validator=DynamicValidator(lambda: self.validator),
            completer=DynamicCompleter(lambda: self.completer),
            history=DynamicHistory(lambda: self.history),
            auto_suggest=DynamicAutoSuggest(lambda: self.auto_suggest),
            accept_handler=accept,
            get_tempfile_suffix=lambda: self.tempfile_suffix)

        search_buffer = Buffer(name=SEARCH_BUFFER, loop=self.loop)

        # Create processors list.
        input_processor = merge_processors([
            ConditionalProcessor(
                # By default, only highlight search when the search
                # input has the focus. (Note that this doesn't mean
                # there is no search: the Vi 'n' binding for instance
                # still allows to jump to the next match in
                # navigation mode.)
                HighlightSearchProcessor(preview_search=True),
                has_focus(search_buffer)),
            HighlightSelectionProcessor(),
            ConditionalProcessor(AppendAutoSuggestion(), has_focus(default_buffer) & ~is_done),
            ConditionalProcessor(PasswordProcessor(), dyncond('is_password')),
            DisplayMultipleCursors(),

            # Users can insert processors here.
            DynamicProcessor(lambda: self.extra_input_processor),

            # For single line mode, show the prompt before the input.
            ConditionalProcessor(
                merge_processors([
                    BeforeInput(get_prompt_tokens_2),
                    ShowArg(),
                ]),
                ~dyncond('multiline'))
        ])

        # Create bottom toolbars.
        bottom_toolbar = ConditionalContainer(
            Window(TokenListControl(lambda app: self.get_bottom_toolbar_tokens(app)),
                                    token=Token.Toolbar,
                                    height=Dimension.exact(1)),
            filter=~is_done & RendererHeightIsKnown() &
                    Condition(lambda app: self.get_bottom_toolbar_tokens is not None))

        search_toolbar = SearchToolbar(search_buffer)
        search_buffer_control = BufferControl(
            buffer=search_buffer,
            input_processor=merge_processors([
                ReverseSearchProcessor(),
                ShowArg(),
            ]))

        def get_search_buffer_control():
            " Return the UIControl to be focussed when searching start. "
            if _true(self.multiline):
                return search_toolbar.control
            else:
                return search_buffer_control

        default_buffer_control = BufferControl(
            buffer=default_buffer,
            get_search_buffer_control=get_search_buffer_control,
            input_processor=input_processor,
            lexer=DynamicLexer(lambda: self.lexer),
            preview_search=True)

        default_buffer_window = Window(
            default_buffer_control,
            get_height=self._get_default_buffer_control_height,
            left_margins=[
                # In multiline mode, use the window margin to display
                # the prompt and continuation tokens.
                ConditionalMargin(
                    PromptMargin(get_prompt_tokens_2, self._get_continuation_tokens),
                    filter=dyncond('multiline'),
                )
            ],
            wrap_lines=dyncond('wrap_lines'))

        # Build the layout.
        layout = HSplit([
            # The main input, with completion menus floating on top of it.
            FloatContainer(
                HSplit([
                    ConditionalContainer(
                        Window(
                            TokenListControl(get_prompt_tokens_1),
                            dont_extend_height=True),
                        Condition(has_before_tokens)
                    ),
                    ConditionalContainer(
                        default_buffer_window,
                        Condition(lambda app:
                            app.layout.current_control != search_buffer_control),
                    ),
                    ConditionalContainer(
                        Window(search_buffer_control),
                        Condition(lambda app:
                            app.layout.current_control == search_buffer_control),
                    ),
                ]),
                [
                    # Completion menus.
                    Float(xcursor=True,
                          ycursor=True,
                          content=CompletionsMenu(
                              max_height=16,
                              scroll_offset=1,
                              extra_filter=has_focus(default_buffer) &
                                  ~dyncond('display_completions_in_columns'),
                    )),
                    Float(xcursor=True,
                          ycursor=True,
                          content=MultiColumnCompletionsMenu(
                              show_meta=True,
                              extra_filter=has_focus(default_buffer) &
                                  dyncond('display_completions_in_columns'),
                    )),
                    # The right prompt.
                    Float(right=0, top=0, hide_when_covering_content=True,
                          content=_RPrompt(self._get_rprompt_tokens)),
                ]
            ),
            ValidationToolbar(),
            SystemToolbar(self.loop, enable=dyncond('enable_system_bindings')),

            # In multiline mode, we use two toolbars for 'arg' and 'search'.
            ConditionalContainer(ArgToolbar(), dyncond('multiline')),
            ConditionalContainer(search_toolbar, dyncond('multiline')),
            bottom_toolbar,
        ])

        # Default key bindings.
        default_bindings = load_key_bindings(
            enable_abort_and_exit_bindings=True,
            enable_search=True,
            enable_auto_suggest_bindings=True,
            enable_system_bindings=dyncond('enable_system_bindings'),
            enable_open_in_editor=dyncond('enable_open_in_editor'))
        prompt_bindings = KeyBindings()

        @Condition
        def do_accept(app):
            return (not _true(self.multiline) and
                    self.app.layout.current_control == self._default_buffer_control)

        @prompt_bindings.add(Keys.Enter, filter=do_accept)
        def _(event):
            " Accept input when enter has been pressed. "
            self._default_buffer.validate_and_handle(event.app)

        # Create application
        application = Application(
            layout=Layout(layout, default_buffer_window),
            style=DynamicStyle(lambda: self.style or DEFAULT_STYLE),
            clipboard=DynamicClipboard(lambda: self.clipboard),
            key_bindings=merge_key_bindings([
                ConditionalKeyBindings(
                    merge_key_bindings([default_bindings, prompt_bindings]),
                    dyncond('include_default_key_bindings')),
                DynamicKeyBindings(lambda: self.extra_key_bindings),
            ]),
            get_title=self._get_title,
            mouse_support=dyncond('mouse_support'),
            editing_mode=editing_mode,
            erase_when_done=erase_when_done,
            reverse_vi_search_direction=True,

            # I/O.
            loop=self.loop,
            input=self.input,
            output=self.output)

        # During render time, make sure that we focus the right search control
        # (if we are searching). - This could be useful if people make the
        # 'multiline' property dynamic.
        '''
        def on_render(app):
            multiline = _true(self.multiline)
            current_control = app.layout.current_control

            if multiline:
                if current_control == search_buffer_control:
                    app.layout.current_control = search_toolbar.control
                    app.invalidate()
            else:
                if current_control == search_toolbar.control:
                    app.layout.current_control = search_buffer_control
                    app.invalidate()

        app.on_render += on_render
        '''

        return application, default_buffer, default_buffer_control

    def _auto_refresh_context(self):
        " Return a context manager for the auto-refresh loop. "
        # Set up refresh interval.
        class _Refresh(object):
            def __enter__(ctx):
                self.done = False

                def run():
                    while not self.done:
                        time.sleep(self.refresh_interval)
                        self.app.invalidate()

                if self.refresh_interval:
                    t = threading.Thread(target=run)
                    t.daemon = True
                    t.start()

            def __exit__(ctx, *a):
                self.done = True

        return _Refresh()

    def _patch_context(self):
        if self.patch_stdout:
            return self.app.patch_stdout_context(raw=True)
        else:
            return DummyContext()

    def prompt(
            self, message=None,
            # When any of these arguments are passed, this value is overwritten for the current prompt.
            default='', patch_stdout=None, true_color=None, editing_mode=None,
            refresh_interval=None, vi_mode=None, lexer=None, completer=None,
            is_password=None, extra_key_bindings=None, include_default_key_bindings=None,
            get_bottom_toolbar_tokens=None, style=None, get_prompt_tokens=None,
            get_rprompt_tokens=None, multiline=None,
            get_continuation_tokens=None, wrap_lines=None, history=None,
            enable_history_search=None,
            complete_while_typing=None, display_completions_in_columns=None,
            auto_suggest=None, validator=None, clipboard=None,
            mouse_support=None, get_title=None, extra_input_processor=None,
            reserve_space_for_menu=None,
            enable_system_bindings=False, enable_open_in_editor=False,
            tempfile_suffix=None):
        """
        Display the prompt.
        """
        # Backup original settings.
        backup = dict((name, getattr(self, name)) for name in self._fields)

        # Take settings from 'prompt'-arguments.
        for name in self._fields:
            value = locals()[name]
            if value is not None:
                setattr(self, name, value)

        if vi_mode:
            self.editing_mode = EditingMode.VI


        with self._auto_refresh_context():
            with self._patch_context():
                try:
                    self._default_buffer.reset(Document(self.default))
                    return self.app.run()
                finally:
                    # Restore original settings.
                    for name in self._fields:
                        setattr(self, name, backup[name])

    try:
        exec_(textwrap.dedent('''
    async def prompt_async(self, message=None,
            # When any of these arguments are passed, this value is overwritten for the current prompt.
            default='', patch_stdout=None, true_color=None, editing_mode=None,
            refresh_interval=None, vi_mode=None, lexer=None, completer=None,
            is_password=None, extra_key_bindings=None, include_default_key_bindings=None,
            get_bottom_toolbar_tokens=None, style=None, get_prompt_tokens=None,
            get_rprompt_tokens=None, multiline=None,
            get_continuation_tokens=None, wrap_lines=None, history=None,
            enable_history_search=None,
            complete_while_typing=None, display_completions_in_columns=None,
            auto_suggest=None, validator=None, clipboard=None,
            mouse_support=None, get_title=None, extra_input_processor=None,
            reserve_space_for_menu=None,
            enable_system_bindings=False, enable_open_in_editor=False,
            tempfile_suffix=None):
        """
        Display the prompt (run in async IO coroutine).
        This is only available in Python 3.5 or newer.
        """
        # Backup original settings.
        backup = dict((name, getattr(self, name)) for name in self._fields)

        # Take settings from 'prompt'-arguments.
        for name in self._fields:
            value = locals()[name]
            if value is not None:
                setattr(self, name, value)

        if vi_mode:
            self.editing_mode = EditingMode.VI

        with self._auto_refresh_context():
            with self._patch_context():
                try:
                    self._default_buffer.reset(Document(self.default))
                    return await self.app.run_async()
                finally:
                    # Restore original settings.
                    for name in self._fields:
                        setattr(self, name, backup[name])
        '''), globals(), locals())
    except SyntaxError:
        def prompt_async(self, *a, **kw):
            """
            Display the prompt (run in async IO coroutine).
            This is only available in Python 3.5 or newer.
            """
            raise NotImplementedError

    @property
    def editing_mode(self):
        return self.app.editing_mode

    @editing_mode.setter
    def editing_mode(self, value):
        self.app.editing_mode = value

    def _get_default_buffer_control_height(self, app):
        # If there is an autocompletion menu to be shown, make sure that our
        # layout has at least a minimal height in order to display it.
        if self.completer is not None:
            space = self.reserve_space_for_menu
        else:
            space = 0

        if space and not app.is_done:
            buff = self._default_buffer

            # Reserve the space, either when there are completions, or when
            # `complete_while_typing` is true and we expect completions very
            # soon.
            if buff.complete_while_typing() or buff.complete_state is not None:
                return Dimension(min=space)

        return Dimension()

    def _get_prompt_tokens(self, app):
        if self.get_prompt_tokens is None:
            return [(Token.Prompt, self.message or '')]
        else:
            return self.get_prompt_tokens(app)

    def _get_rprompt_tokens(self, app):
        if self.get_rprompt_tokens:
            return self.get_rprompt_tokens(app)
        return []

    def _get_continuation_tokens(self, app, width):
        if self.get_continuation_tokens:
            return self.get_continuation_tokens(app, width)
        return []

    def _get_title(self):
        if self.get_title is None:
            return
        else:
            return self.get_title()

    def close(self):
        return#self.loop.close()


def prompt(*a, **kw):
    """ The global `prompt` function. This will create a new `Prompt` instance
    for every call.  """
    prompt = Prompt()
    try:
        return prompt.prompt(*a, **kw)
    finally:
        prompt.close()

prompt.__doc__ = Prompt.prompt.__doc__


try:
    exec_(textwrap.dedent('''
    async def prompt_async(*a, **kw):
        """
        Similar to :func:`.prompt`, but return an asyncio coroutine instead.
        """
        loop = create_asyncio_event_loop()
        prompt = Prompt(loop=loop)
        try:
            return await prompt.prompt_async(*a, **kw)
        finally:
            prompt.close()
    prompt_async.__doc__ = Prompt.prompt_async
    '''), globals(), locals())
except SyntaxError:
    def prompt_async(*a, **kw):
        raise NotImplementedError(
            'prompt_async is only available for Python >3.5.')


def create_confirm_prompt(message, loop=None):
    """
    Create a `Prompt` object for the 'confirm' function.
    """
    assert isinstance(message, text_type)
    bindings = KeyBindings()

    @bindings.add('y')
    @bindings.add('Y')
    def _(event):
        prompt._default_buffer.text = 'y'
        event.app.set_return_value(True)

    @bindings.add('n')
    @bindings.add('N')
    @bindings.add(Keys.ControlC)
    def _(event):
        prompt._default_buffer.text = 'n'
        event.app.set_return_value(False)

    prompt = Prompt(message, extra_key_bindings=bindings,
                    include_default_key_bindings=False,
                    loop=loop)
    return prompt


def confirm(message='Confirm (y or n) '):
    """
    Display a confirmation prompt that returns True/False.
    """
    p = create_confirm_prompt(message)
    try:
        return p.prompt()
    finally:
        p.close()
