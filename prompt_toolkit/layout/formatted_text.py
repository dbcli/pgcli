from __future__ import unicode_literals
import six
import xml.dom.minidom as minidom

__all__ = (
    'to_formatted_text',
    'HTML',
)


def to_formatted_text(value, style=''):
    """
    Convert the given value (which can be formatted text) into a list of text
    fragments. (Which is the canonical form of formatted text.) The outcome is
    supposed to be a list of (style, text) tuples.

    It can take an `HTML` object, a plain text string, or anything that
    implements `__pt_formatted_text__`.

    :param style: An additional style string which is applied to all text
        fragments.
    """
    assert isinstance(style, six.text_type)

    if isinstance(value, six.text_type):
        result = [('', value)]
    elif isinstance(value, list):
        if len(value):
            assert isinstance(value[0][0], six.text_type)
            assert isinstance(value[0][1], six.text_type)
        result = value
    elif hasattr(value, '__pt_formatted_text__'):
        result = value.__pt_formatted_text__()
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
