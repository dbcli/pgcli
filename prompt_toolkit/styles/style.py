"""
Tool for creating styles from a dictionary.
"""
from __future__ import unicode_literals, absolute_import
import itertools
import re
from .base import BaseStyle, DEFAULT_ATTRS, ANSI_COLOR_NAMES, Attrs

__all__ = (
    'Style',
)


def _colorformat(text):
    """
    Parse/validate color format.

    Like in Pygments, but also support the ANSI color names.
    (These will map to the colors of the 16 color palette.)
    """
    if text[0:1] == '#':
        col = text[1:]
        if col in ANSI_COLOR_NAMES:
            return col
        elif len(col) == 6:
            return col
        elif len(col) == 3:
            return col[0]*2 + col[1]*2 + col[2]*2
    elif text in ('', 'default'):
        return text

    raise ValueError('Wrong color format %r' % text)


# Attributes, when they are not filled in by a style. None means that we take
# the value from the parent.
_EMPTY_ATTRS = Attrs(color=None, bgcolor=None, bold=None, underline=None,
                     italic=None, blink=None, reverse=None)


def _expand_classname(classname):
    """
    Split a single class name at the `.` operator, and build a list of classes.

    E.g. 'a.b.c' becomes ['a', 'a.b', 'a.b.c']
    """
    result = []
    parts = classname.split('.')

    for i in range(1, len(parts) + 1):
        result.append('.'.join(parts[:i]).lower())

    return result


def _parse_style_str(style_str):
    """
    Take a style string, e.g.  'bg:red #88ff00 class:title'
    and return a `Attrs` instance.
    """
    # Start from default Attrs.
    if 'noinherit' in style_str:
        attrs = DEFAULT_ATTRS
    else:
        attrs = _EMPTY_ATTRS

    # Now update with the given attributes.
    for part in style_str.split():
        if part == 'noinherit':
            pass
        elif part == 'bold':
            attrs = attrs._replace(bold=True)
        elif part == 'nobold':
            attrs = attrs._replace(bold=False)
        elif part == 'italic':
            attrs = attrs._replace(italic=True)
        elif part == 'noitalic':
            attrs = attrs._replace(italic=False)
        elif part == 'underline':
            attrs = attrs._replace(underline=True)
        elif part == 'nounderline':
            attrs = attrs._replace(underline=False)

        # prompt_toolkit extensions. Not in Pygments.
        elif part == 'blink':
            attrs = attrs._replace(blink=True)
        elif part == 'noblink':
            attrs = attrs._replace(blink=False)
        elif part == 'reverse':
            attrs = attrs._replace(reverse=True)
        elif part == 'noreverse':
            attrs = attrs._replace(reverse=False)

        # Pygments properties that we ignore.
        elif part in ('roman', 'sans', 'mono'):
            pass
        elif part.startswith('border:'):
            pass

        # Ignore pieces in between square brackets. This is internal stuff.
        # Like '[transparant]' or '[set-cursor-position]'.
        elif part.startswith('[') and part.endswith(']'):
            pass

        # Colors.
        elif part.startswith('bg:'):
            attrs = attrs._replace(bgcolor=_colorformat(part[3:]))
        elif part.startswith('fg:'):  # The 'fg:' prefix is optional.
            attrs = attrs._replace(color=_colorformat(part[3:]))
        else:
            attrs = attrs._replace(color=_colorformat(part))

    return attrs


CLASS_NAMES_RE = re.compile(r'^[a-z0-9.\s-]*$')  # This one can't contain a comma!


class Style(BaseStyle):
    """
    Create a ``Style`` instance from a list of style rules.

    The `style_rules` is supposed to be a list of ('classnames', 'style') tuples.
    The classnames are a whitespace separated string of class names and the
    style string is just like a Pygments style definition, but with a few
    additions: it supports 'reverse' and 'blink'.

    Usage::

        Style([
            ('title', '#ff0000 bold underline'),
            ('something-else', 'reverse'),
            ('class1 class2', 'reverse'),
        ])

    The ``from_dict`` classmethod is similar, but takes a dictionary as input.
    """
    def __init__(self, style_rules):
        assert isinstance(style_rules, list)

        class_names_and_attrs = []

        # Loop through the rules in the order they were defined.
        # Rules that are defined later get priority.
        for class_names, style_str in style_rules:
            assert CLASS_NAMES_RE.match(class_names), repr(class_names)

            # The order of the class names doesn't matter.
            # (But the order of rules does matter.)
            class_names = frozenset(class_names.lower().split())
            attrs = _parse_style_str(style_str)

            class_names_and_attrs.append((class_names, attrs))

        self.class_names_and_attrs = class_names_and_attrs

    @classmethod
    def from_dict(cls, style_dict):
        """
        :param include_defaults: Include the defaults (built-in) styling for
            selected text, etc...)
        """
        return cls(list(style_dict.items()))

    def get_attrs_for_style_str(self, style_str, default=DEFAULT_ATTRS):
        """
        Get `Attrs` for the given style string.
        """
        list_of_attrs = [default]
        class_names = set()

        # Apply default styling.
        for names, attr in self.class_names_and_attrs:
            if not names:
                list_of_attrs.append(attr)

        # Go from left to right through the style string. Things on the right
        # take precedence.
        for part in style_str.split():
            # This part represents a class.
            # Do lookup of this class name in the style definition, as well
            # as all class combinations that we have so far.
            if part.startswith('class:'):
                # Expand all class names (comma separated list).
                new_class_names = []
                for p in part[6:].lower().split(','):
                    new_class_names.extend(_expand_classname(p))

                for new_name in new_class_names:
                    # Build a set of all possible class combinations to be applied.
                    combos = set()
                    combos.add(frozenset([new_name]))

                    for count in range(1, len(class_names) + 1):
                        for c2 in itertools.combinations(class_names, count):
                            combos.add(frozenset(c2 + (new_name, )))

                    # Apply the styles that match these class names.
                    for names, attr in self.class_names_and_attrs:
                        if names in combos:
                            list_of_attrs.append(attr)

                    class_names.add(new_name)

            # Process inline style.
            else:
                inline_attrs = _parse_style_str(part)
                list_of_attrs.append(inline_attrs)

        return _merge_attrs(list_of_attrs)

    def invalidation_hash(self):
        return id(self.class_names_and_attrs)


def _merge_attrs(list_of_attrs):
    """
    Take a list of :class:`.Attrs` instances and merge them into one.
    Every `Attr` in the list can override the styling of the previous one. So,
    the last one has highest priority.
    """
    def _or(*values):
        " Take first not-None value, starting at the end. "
        for v in values[::-1]:
            if v is not None:
                return v

    return Attrs(
        color=_or('', *[a.color for a in list_of_attrs]),
        bgcolor=_or('', *[a.bgcolor for a in list_of_attrs]),
        bold=_or(False, *[a.bold for a in list_of_attrs]),
        underline=_or(False, *[a.underline for a in list_of_attrs]),
        italic=_or(False, *[a.italic for a in list_of_attrs]),
        blink=_or(False, *[a.blink for a in list_of_attrs]),
        reverse=_or(False, *[a.reverse for a in list_of_attrs]))
