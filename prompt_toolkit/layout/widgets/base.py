"""
Collection of reusable components for building full screen applications.

All of these widgets implement the ``__pt_container__`` method, which makes
them usable in any situation where we are expecting a `prompt_toolkit`
container object.
"""
from __future__ import unicode_literals
from functools import partial
import six

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.eventloop import EventLoop, get_event_loop
from prompt_toolkit.filters import to_app_filter
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.utils import get_cwidth

from ..containers import Window, VSplit, HSplit, FloatContainer, Float, Align
from ..controls import BufferControl, FormattedTextControl
from ..dimension import Dimension as D
from ..dimension import to_dimension
from ..margins import ScrollbarMargin
from ..processors import PasswordProcessor, ConditionalProcessor, HighlightSearchProcessor, HighlightSelectionProcessor, DisplayMultipleCursors, BeforeInput, merge_processors


__all__ = (
    'TextArea',
    'Label',
    'Button',
    'Frame',
    'Shadow',
    'Box',
    'VerticalLine',
    'HorizontalLine',
    'RadioList',

    'Checkbox',  # XXX: refactor into CheckboxList.
    'ProgressBar',
)


class BORDER:
    " Box drawing characters. (Thin) "
    HORIZONTAL = '\u2500'
    VERTICAL = '\u2502'
    TOP_LEFT = '\u250c'
    TOP_RIGHT = '\u2510'
    BOTTOM_LEFT = '\u2514'
    BOTTOM_RIGHT = '\u2518'


class TextArea(object):
    """
    A simple input field.

    This contains a ``prompt_toolkit`` ``Buffer`` object that hold the text
    data structure for the edited buffer, the ``BufferControl``, which applies
    a ``Lexer`` to the text and turns it into a ``UIControl``, and finally,
    this ``UIControl`` is wrapped in a ``Window`` object (just like any
    ``UIControl``), which is responsible for the scrolling.

    This widget does have some options, but it does not intend to cover every
    single use case. For more configurations options, you can always build a
    text area manually, using a ``Buffer``, ``BufferControl`` and ``Window``.

    :param text: The initial text.
    :param multiline: If True, allow multiline input.
    :param lexer: ``Lexer`` instance for syntax highlighting.
    :param completer: ``Completer`` instance for auto completion.
    :param focussable: When `True`, allow this widget to receive the focus.
    :param wrap_lines: When `True`, don't scroll horizontally, but wrap lines.
    :param width: Window width. (``Dimension`` object.)
    :param height: Window height. (``Dimension`` object.)
    :param password: When `True`, display using asteriks.
    :param accept_handler: Called when `Enter` is pressed.
    :param scrollbar: When `True`, display a scroll bar.
    :param style: A style string.
    :param dont_extend_height:
    :param dont_extend_width:
    :param loop: The `EventLoop` to be used.
    """
    def __init__(self, text='', multiline=True, password=False,
                 lexer=None, completer=None, accept_handler=None,
                 focussable=True, wrap_lines=True,
                 width=None, height=None,
                 dont_extend_height=False, dont_extend_width=False,
                 scrollbar=False, style='', input_processor=None,
                 prompt='', loop=None, _label=False):
        assert isinstance(text, six.text_type)
        assert loop is None or isinstance(loop, EventLoop)

        loop = loop or get_event_loop()

        def get_prompt_text_fragments(app):
            return [('class:text-area.prompt', prompt)]

        self.buffer = Buffer(
            loop=loop,
            document=Document(text, 0),
            multiline=multiline,
            completer=completer,
            complete_while_typing=True,
            accept_handler=lambda app, buffer: accept_handler(app))

        self.control = BufferControl(
            buffer=self.buffer,
            lexer=lexer,
            input_processor=merge_processors([
                ConditionalProcessor(
                    processor=PasswordProcessor(),
                    filter=to_app_filter(password)
                ),
                HighlightSearchProcessor(),
                HighlightSelectionProcessor(),
                DisplayMultipleCursors(),
                BeforeInput(get_text_fragments=get_prompt_text_fragments),
            ]),
            focussable=focussable)

        if multiline:
            if scrollbar:
                margins = [ScrollbarMargin(display_arrows=True)]
            else:
                margins = []
        else:
            height = D.exact(1)
            margins = []

        if not _label:
            # (In case of a Label, we don't want to apply the text-area style.)
            style = 'class:text-area ' + style

        self.window = Window(
            height=height,
            width=width,
            dont_extend_height=dont_extend_height,
            dont_extend_width=dont_extend_width,
            content=self.control,
            style=style,
            wrap_lines=wrap_lines,
            right_margins=margins)

    @property
    def text(self):
        return self.buffer.text

    @text.setter
    def text(self, value):
        self.buffer.document = Document(value, 0)

    @property
    def document(self):
        return self.buffer.document

    @document.setter
    def document(self, value):
        self.buffer.document = value

    def __pt_container__(self):
        return self.window


class Label(object):
    """
    Widget that displays the given text. It is not editable or focussable.

    :param text: The text to be displayed. (This can be multiline.)
    :param style: A style string.
    :param width: When given, use this width, rather than calculating it from
        the text size.
    :param loop: The `EventLoop` to be used.
    """
    def __init__(self, text, style='', width=None, loop=None,
                 dont_extend_height=True, dont_extend_width=False):
        assert isinstance(text, six.text_type)
        assert loop is None or isinstance(loop, EventLoop)

        if width is None:
            longest_line = max(get_cwidth(line) for line in text.splitlines())
            width = D(preferred=longest_line)

        self.text_area = TextArea(
            text=text,
            width=width,
            style='class:label ' + style,
            focussable=False,
            dont_extend_height=dont_extend_height,
            dont_extend_width=dont_extend_width,
            loop=loop,
            _label=True)

        loop = loop or get_event_loop()

    @property
    def text(self):
        return self.text_area.buffer.text

    @text.setter
    def text(self, value):
        self.text_area.buffer.text = value

    def __pt_container__(self):
        return self.text_area


class Button(object):
    """
    Clickable button.

    :param text: The caption for the button.
    :param handler: `None` or callable. Called when the button is clicked.
    :param width: Width of the button.
    :param loop: The `EventLoop` to be used.
    """
    def __init__(self, text, handler=None, width=12, loop=None):
        assert isinstance(text, six.text_type)
        assert handler is None or callable(handler)
        assert isinstance(width, int)
        assert loop is None or isinstance(loop, EventLoop)

        self.text = text
        self.handler = handler
        self.width = width
        self.control = FormattedTextControl(
            self._get_text_fragments,
            key_bindings=self._get_key_bindings(),
            focussable=True)

        self.window = Window(
            self.control,
            align=Align.CENTER,
            height=1,
            width=width,
            style='class:button',
            dont_extend_width=True,
            dont_extend_height=True)

    def _get_text_fragments(self, app):
        text = ('{:^%s}' % (self.width - 2)).format(self.text)

        return [
            ('class:button.arrow', '<', self.handler),
            ('class:button.text', text, self.handler),
            ('class:button.arrow', '>', self.handler),
        ]

    def _get_key_bindings(self):
        " Key bindings for the Button. "
        kb = KeyBindings()

        @kb.add(' ')
        @kb.add('enter')
        def _(event):
            if self.handler is not None:
                self.handler(event.app)

        return kb

    def __pt_container__(self):
        return self.window


class Frame(object):
    """
    Draw a border around any container.

    :param body: Another container object.
    :param title: Text to be displayed in the top of the frame.
    :param loop: The `EventLoop` to be used.
    """
    def __init__(self, body, title='', style='', loop=None):
        assert loop is None or isinstance(loop, EventLoop)

        loop = loop or get_event_loop()

        fill = partial(Window, style='class:frame-border')
        style = 'class:frame ' + style

        if title:
            top_row = VSplit([
                fill(width=1, height=1, char=BORDER.TOP_LEFT),
                fill(char=BORDER.HORIZONTAL),
                fill(width=1, height=1, char='|'),
                Label(' {} '.format(title), style='class:frame-label', loop=loop,
                      dont_extend_width=True),
                fill(width=1, height=1, char='|'),
                fill(char=BORDER.HORIZONTAL),
                fill(width=1, height=1, char=BORDER.TOP_RIGHT),
            ])
        else:
            top_row = VSplit([
                fill(width=1, height=1, char=BORDER.TOP_LEFT),
                fill(char=BORDER.HORIZONTAL),
                fill(width=1, height=1, char=BORDER.TOP_RIGHT),
            ])

        self.container = HSplit([
            top_row,
            VSplit([
                fill(width=1, char=BORDER.VERTICAL),
                body,
                fill(width=1, char=BORDER.VERTICAL),
                    # Padding is required to make sure that if the content is
                    # too small, that the right frame border is still aligned.
            ], padding=D(preferred=0)),
            VSplit([
                fill(width=1, height=1, char=BORDER.BOTTOM_LEFT),
                fill(char=BORDER.HORIZONTAL),
                fill(width=1, height=1, char=BORDER.BOTTOM_RIGHT),
            ]),
        ], style=style)

    def __pt_container__(self):
        return self.container


class Shadow(object):
    """
    Draw a shadow underneath/behind this container.
    (This applies `class:shadow` the the cells under the shadow. The Style
    should define the colors for the shadow.)

    :param body: Another container object.
    """
    def __init__(self, body):
        self.container = FloatContainer(
            content=body,
            floats=[
                Float(bottom=-1, height=1, left=1, right=-1,
                      content=Window(style='class:shadow')),
                Float(bottom=-1, top=1, width=1, right=-1,
                      content=Window(style='class:shadow')),
                ]
            )

    def __pt_container__(self):
        return self.container


class Box(object):
    """
    Add padding around a container.

    This also makes sure that the parent can provide more space than required by
    the child. This is very useful when wrapping a small element with a fixed
    size into a ``VSplit`` or ``HSplit`` object. The ``HSplit`` and ``VSplit``
    try to make sure to adapt respectively the width and height, possibly
    shrinking other elements. Wrapping something in a ``Box`` makes it flexible.

    :param body: Another container object.
    :param padding: The margin to be used around the body. This can be
        overridden by `padding_left`, padding_right`, `padding_top` and
        `padding_bottom`.
    :param style: A style string.
    :param char: Character to be used for filling the space around the body.
        (This is supposed to be a character with a terminal width of 1.)
    """
    def __init__(self, body, padding=None,
                 padding_left=None, padding_right=None,
                 padding_top=None, padding_bottom=None,
                 width=None, height=None,
                 style='', char=None):
        if padding is None:
            padding = D(preferred=0)

        def get(value):
            if value is None:
                value = padding
            return to_dimension(value)

        self.padding_left = get(padding_left)
        self.padding_right = get(padding_right)
        self.padding_top = get(padding_top)
        self.padding_bottom = get(padding_bottom)
        self.body = body

        self.container = HSplit([
            Window(height=self.padding_top, char=char),
            VSplit([
                Window(width=self.padding_left, char=char),
                body,
                Window(width=self.padding_right, char=char),
            ]),
            Window(height=self.padding_bottom, char=char),
        ], width=width, height=height, style=style)

    def __pt_container__(self):
        return self.container


class Checkbox(object):
    def __init__(self, text='', loop=None):
        assert loop is None or isinstance(loop, EventLoop)

        loop = loop or get_event_loop()

        self.checked = True

        kb = KeyBindings()

        @kb.add(' ')
        @kb.add('enter')
        def _(event):
            self.checked = not self.checked

        self.control = FormattedTextControl(
            self._get_text_fragments,
            key_bindings=kb,
            focussable=True)

        self.window = Window(width=3, content=self.control)

        self.container = VSplit([
            self.window,
            Label(loop=loop, text=' {}'.format(text))
        ], style='class:checkbox')

    def _get_text_fragments(self, app):
        text = '*' if self.checked else ' '
        return [('', '[%s]' % text)]

    def __pt_container__(self):
        return self.container


class RadioList(object):
    """
    List of radio buttons. Only one can be checked at the same time.

    :param values: List of (value, label) tuples.
    :param loop: The `EventLoop` to be used.
    """
    def __init__(self, values, loop=None):
        assert isinstance(values, list)
        assert len(values) > 0
        assert all(isinstance(i, tuple) and len(i) == 2
                   for i in values)
        assert loop is None or isinstance(loop, EventLoop)

        loop = loop or get_event_loop()

        self.values = values
        self.current_value = values[0][0]
        self._selected_index = 0

        # Key bindings.
        kb = KeyBindings()

        @kb.add('up')
        def _(event):
            self._selected_index = max(0, self._selected_index - 1)

        @kb.add('down')
        def _(event):
            self._selected_index = min(
                len(self.values) - 1, self._selected_index + 1)

        @kb.add('enter')
        @kb.add(' ')
        def _(event):
            self.current_value = self.values[self._selected_index][0]

        # Control and window.
        self.control = FormattedTextControl(
            self._get_text_fragments,
            key_bindings=kb,
            focussable=True)

        self.window = Window(
            content=self.control,
            style='class:radio-list',
            right_margins=[
                ScrollbarMargin(display_arrows=True),
            ],
            dont_extend_height=True)

    def _get_text_fragments(self, app):
        result = []
        for i, value in enumerate(self.values):
            checked = (value[0] == self.current_value)
            selected = (i == self._selected_index)

            style = ''
            if checked:
                style += ' class:radio-checked'
            if selected:
                style += ' class:radio-selected'

            result.append((style, '('))

            if selected:
                result.append(('[SetCursorPosition]', ''))

            if checked:
                result.append((style, '*'))
            else:
                result.append((style, ' '))

            result.append((style, ')'))
            result.append(('class:radio', ' '))
            result.append(('class:radio', value[1]))
            result.append(('', '\n'))

        return result

    def __pt_container__(self):
        return self.window


class VerticalLine(object):
    """
    A simple vertical line with a width of 1.
    """
    def __init__(self):
        self.window = Window(
            char=BORDER.VERTICAL,
            style='class:line,vertical-line',
            width=1)

    def __pt_container__(self):
        return self.window


class HorizontalLine(object):
    """
    A simple horizontal line with a height of 1.
    """
    def __init__(self):
        self.window = Window(
            char=BORDER.HORIZONTAL,
            style='class:line,horizontal-line',
            height=1)

    def __pt_container__(self):
        return self.window


class ProgressBar(object):
    def __init__(self, loop=None):
        loop = loop or get_event_loop()
        self._percentage = 60

        self.label = Label('60%')
        self.container = FloatContainer(
            content=Window(height=1),
            floats=[
                # We first draw the label, than the actual progress bar.  Right
                # now, this is the only way to have the colors of the progress
                # bar appear on to of the label. The problem is that our label
                # can't be part of any `Window` below.
                Float(content=self.label, top=0, bottom=0),

                Float(left=0, top=0, right=0, bottom=0, content=VSplit([
                    Window(style='class:progress-bar.used', get_width=lambda app: D(weight=int(self._percentage))),
                    Window(style='class:progress-bar', get_width=lambda app: D(weight=int(100 - self._percentage))),
                ])),
            ])

    @property
    def percentage(self):
        return self._percentage

    @percentage.setter
    def percentage(self, value):
        assert isinstance(value, int)
        self._percentage = value
        self.label.text = '{}%'.format(value)

    def __pt_container__(self):
        return self.container
