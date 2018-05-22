from __future__ import unicode_literals
import six
import xml.dom.minidom as minidom

__all__ = [
    'HTML'
]


class HTML(object):
    """
    HTML formatted text.
    Take something HTML-like, for use as a formatted string.

    ::

        # Turn something into red.
        HTML('<style fg="ansired" bg="#00ff44">...</style>')

        # Italic, bold and underline.
        HTML('<i>...</i>')
        HTML('<b>...</b>')
        HTML('<u>...</u>')

    All HTML elements become available as a "class" in the style sheet.
    E.g. ``<username>...</username>`` can be styled, by setting a style for
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
                        if k == 'color': fg = v  # Alias for 'fg'.

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

    def format(self, *args, **kwargs):
        """
        Like `str.format`, but make sure that the arguments are properly
        escaped.
        """
        # Escape all the arguments.
        args = [html_escape(a) for a in args]
        kwargs = dict((k, html_escape(v)) for k, v in kwargs.items())

        return HTML(self.value.format(*args, **kwargs))

    def __mod__(self, value):
        """
        HTML('<b>%s</b>') % value
        """
        if not isinstance(value, tuple):
            value = (value, )

        value = tuple(html_escape(i) for i in value)
        return HTML(self.value % value)


def html_escape(text):
    # The string interpolation functions also take integers and other types.
    # Convert to string first.
    if not isinstance(text, six.text_type):
        text = '{}'.format(text)

    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
