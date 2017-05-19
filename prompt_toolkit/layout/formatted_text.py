"""
Many places in prompt_toolkit can take either plain text, or formatted text.
For instance the ``shortcuts.prompt()`` function takes either plain text or
formatted text for the prompt. The ``FormattedTextControl`` can also take
either plain text or formatted text.

In any case, there is an input that can either be just plain text (a string),
an `HTML` object, an `ANSI` object or a sequence of ``(style_string, text)``
tuples. The ``to_formatted_text`` conversion function takes any of these and
turns all of them into such a tuple sequence.
"""
from __future__ import unicode_literals
from prompt_toolkit.output.vt100 import FG_ANSI_COLORS, BG_ANSI_COLORS
from prompt_toolkit.output.vt100 import _256_colors as _256_colors_table

import six
import xml.dom.minidom as minidom

__all__ = (
    'to_formatted_text',
    'HTML',
    'ANSI',
)


def to_formatted_text(value, app, style=''):
    """
    Convert the given value (which can be formatted text) into a list of text
    fragments. (Which is the canonical form of formatted text.) The outcome is
    supposed to be a list of (style, text) tuples.

    It can take an `HTML` object, a plain text string, or anything that
    implements `__pt_formatted_text__`.

    :param app: The `Applicatin` object.
    :param style: An additional style string which is applied to all text
        fragments.
    """
    # NOTE: The reason that we require `app` to be passed around here, is that
    #       in many situations the value of the formatted string depends on the
    #       value of 'app'. (E.g. `MenuContainer._get_menu_fragments` displays
    #       a different value, depending on whether it's focussed or not. It
    #       needs a reference to 'app' for this.)
    assert isinstance(style, six.text_type)

    if value is None:
        return []
    elif isinstance(value, six.text_type):
        result = [('', value)]
    elif isinstance(value, list):
        if len(value):
            assert isinstance(value[0][0], six.text_type)
            assert isinstance(value[0][1], six.text_type)
        result = value
    elif hasattr(value, '__pt_formatted_text__'):
        result = value.__pt_formatted_text__()
    elif callable(value):
        return to_formatted_text(value(app), app, style=style)
    else:
        raise ValueError('No formatted text given. Expecting a unicode object, '
                         'a list of text fragments or an HTML object.')

    # Apply extra style.
    if style:
        result = [(style + ' ' + k, v) for k, v in result]
    return result


class HTML(object):
    """
    HTML formatted text.
    Take something HTML-like, for use as a formatted string.

    ::

        <!-- Turn something into red. -->
        <style fg="ansired" bg="#00ff44">...</style>

        <!-- Italic, bold and underline.  -->
        <i>...</i>
        <b>...</b>
        <u>...</u>

    All HTML elements become available as a "class" in the style sheet.
    E.g. ``<username>...</username>`` can be styles, by setting a style for
    ``username``.
    """
    def __init__(self, value):
        assert isinstance(value, six.text_type)
        self.value = value
        document = minidom.parseString('<html-root>%s</html-root>' % (value, ))

        result = []
        name_stack = []
        fg_stack = []
        bg_stack = []

        def get_current_style():
            " Build style string for current node. "
            parts = []
            if name_stack:
                parts.append('class:' + ','.join(name_stack))

            if fg_stack:
                parts.append('fg:' + fg_stack[-1])
            if bg_stack:
                parts.append('bg:' + bg_stack[-1])
            return ' '.join(parts)

        def process_node(node):
            " Process node recursively. "
            for child in node.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    result.append((get_current_style(), child.data))
                else:
                    add_to_name_stack = child.nodeName not in ('#document', 'html-root', 'style')
                    fg = bg = ''

                    for k, v in child.attributes.items():
                        if k == 'fg': fg = v
                        if k == 'bg': bg = v

                    # Check for spaces in attributes. This would result in
                    # invalid style strings otherwise.
                    if ' ' in fg: raise ValueError('"fg" attribute contains a space.')
                    if ' ' in bg: raise ValueError('"bg" attribute contains a space.')

                    if add_to_name_stack: name_stack.append(child.nodeName)
                    if fg: fg_stack.append(fg)
                    if bg: bg_stack.append(bg)

                    process_node(child)

                    if add_to_name_stack: name_stack.pop()
                    if fg: fg_stack.pop()
                    if bg: bg_stack.pop()

        process_node(document)

        self.formatted_text = result

    def __repr__(self):
        return 'HTML(%r)' % (self.value, )

    def __pt_formatted_text__(self):
        return self.formatted_text


class ANSI(object):
    """
    ANSI formatted text.
    Take something ANSI escaped text, for use as a formatted string.

    Characters between \001 and \002 are supposed to have a zero width when
    printed, but these are literally sent to the terminal output. This can be
    used for instance, for inserting Final Term prompt commands.
    They will be translated into a prompt_toolkit '[ZeroWidthEscape]' fragment.
    """
    def __init__(self, value):
        self.value = value
        self._formatted_text = []

        # Default style attributes.
        self._color = None
        self._bgcolor = None
        self._bold = False
        self._underline = False
        self._italic = False
        self._blink = False
        self._reverse = False

        # Process received text.
        parser = self._parse_corot()
        parser.send(None)
        for c in value:
            parser.send(c)

    def _parse_corot(self):
        """
        Coroutine that parses the ANSI escape sequences.
        """
        style = ''
        formatted_text = self._formatted_text

        while True:
            csi = False
            c = yield

            # Everything between \001 and \002 should become a ZeroWidthEscape.
            if c == '\001':
                escaped_text = ''
                while c != '\002':
                    c = yield
                    if c == '\002':
                        formatted_text.append(('[ZeroWidthEscape]', escaped_text))
                        c = yield
                        break
                    else:
                        escaped_text += c

            if c == '\x1b':
                # Start of color escape sequence.
                square_bracket = yield
                if square_bracket == '[':
                    csi = True
                else:
                    continue
            elif c == '\x9b':
                csi = True

            if csi:
                # Got a CSI sequence. Color codes are following.
                current = ''
                params = []
                while True:
                    char = yield
                    if char.isdigit():
                        current += char
                    else:
                        params.append(min(int(current or 0), 9999))
                        if char == ';':
                            current = ''
                        elif char == 'm':
                            # Set attributes and token.
                            self._select_graphic_rendition(params)
                            style = self._create_style_string()
                            break
                        else:
                            # Ignore unspported sequence.
                            break
            else:
                # Add current character.
                # NOTE: At this point, we could merge the current character
                #       into the previous tuple if the style did not change,
                #       however, it's not worth the effort given that it will
                #       be "Exploded" once again when it's rendered to the
                #       output.
                formatted_text.append((style, c))

    def _select_graphic_rendition(self, attrs):
        """
        Taken a list of graphics attributes and apply changes.
        """
        replace = {}

        if not attrs:
            attrs = [0]
        else:
            attrs = list(attrs[::-1])

        while attrs:
            attr = attrs.pop()

            if attr in _fg_colors:
                self._color = _fg_colors[attr]
            elif attr in _bg_colors:
                self._bgcolor = _bg_colors[attr]
            elif attr == 1:
                self._bold = True
            elif attr == 3:
                self._italic = True
            elif attr == 4:
                self._underline = True
            elif attr == 5:
                self._blink = True
            elif attr == 6:
                self._blink = True  # Fast blink.
            elif attr == 7:
                self._reverse = True
            elif attr == 22:
                self._bold = False
            elif attr == 23:
                self._italic = False
            elif attr == 24:
                self._underline = False
            elif attr == 25:
                self._blink = False
            elif attr == 27:
                self._reverse = False
            elif not attr:
                self._color = None
                self._bgcolor = None
                self._bold = False
                self._underline = False
                self._italic = False
                self._blink = False
                self._reverse = False

            elif attr in (38, 48):
                n = attrs.pop()

                # 256 colors.
                if n == 5:
                    if attr == 38:
                        m = attrs.pop()
                        self._color = _256_colors.get(m)
                    elif attr == 48:
                        m = attrs.pop()
                        self._bgcolor = _256_colors.get(m)

                # True colors.
                if n == 2:
                    try:
                        color_str = '%02x%02x%02x' % (
                            attrs.pop(), attrs.pop(), attrs.pop())
                    except IndexError:
                        pass
                    else:
                        if attr == 38:
                            self._color = color_str
                        elif attr == 48:
                            self._bgcolor = color_str

    def _create_style_string(self):
        """
        Turn current style flags into a string for usage in a formatted text.
        """
        result = []
        if self._color:
            result.append('#' + self._color)
        if self._bgcolor:
            result.append('bg:#' + self._bgcolor)
        if self._bold:
            result.append('bold')
        if self._underline:
            result.append('underline')
        if self._italic:
            result.append('italic')
        if self._blink:
            result.append('blink')
        if self._reverse:
            result.append('reverse')

        return ' '.join(result)

    def __repr__(self):
        return 'ANSI(%r)' % (self.value, )

    def __pt_formatted_text__(self):
        return self._formatted_text


# Mapping of the ANSI color codes to their names.
_fg_colors = dict((v, k) for k, v in FG_ANSI_COLORS.items())
_bg_colors = dict((v, k) for k, v in BG_ANSI_COLORS.items())

# Mapping of the escape codes for 256colors to their 'ffffff' value.
_256_colors = {}

for i, (r, g, b) in enumerate(_256_colors_table.colors):
    _256_colors[i] = '%02x%02x%02x' % (r, g, b)
