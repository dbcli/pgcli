"""
Tool for creating styles from a dictionary.

This is very similar to the Pygments style dictionary, with some additions:
- Support for reverse and blink.
- Support for ANSI color names. (These will map directly to the 16 terminal
  colors.)
- Any element can have multiple tokens. E.g. Token.A|Token.B.
  The ``|`` operation can be used to combine multiple tokens.
"""
from collections import Mapping
import itertools

from .base import Style, DEFAULT_ATTRS, ANSI_COLOR_NAMES, Attrs
from .defaults import DEFAULT_STYLE_DICTIONARY
from .utils import merge_attrs, split_token_in_parts

__all__ = (
    'style_from_dict',
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


def style_from_dict(style_dict, include_defaults=True):
    """
    Create a ``Style`` instance from a dictionary or other mapping.

    The dictionary is equivalent to the ``Style.styles`` dictionary from
    pygments, with a few additions: it supports 'reverse' and 'blink'.

    Usage::

        style_from_dict({
            Token: '#ff0000 bold underline',
            Token.Title: 'blink',
            Token.SomethingElse: 'reverse',
        })

    :param include_defaults: Include the defaults (built-in) styling for
        selected text, etc...)
    """
    assert isinstance(style_dict, Mapping)

    if include_defaults:
        s2 = {}
        s2.update(DEFAULT_STYLE_DICTIONARY)
        s2.update(style_dict)
        style_dict = s2

    # Expand token inheritance and turn style description into Attrs.
    token_to_attrs = {}

    # (Loop through the tokens in order. Sorting makes sure that
    # we process the parent first.)
    for ttype, styledef in sorted(style_dict.items()):
        important = False

        # Start from default Attrs.
        if 'noinherit' in styledef:
            attrs = DEFAULT_ATTRS
        else:
            attrs = _EMPTY_ATTRS

        # Now update with the given attributes.
        for part in styledef.split():
            if part == 'noinherit':
                pass
            elif part == 'important':
                important = True
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

            # Colors.
            elif part.startswith('bg:'):
                attrs = attrs._replace(bgcolor=_colorformat(part[3:]))
            else:
                attrs = attrs._replace(color=_colorformat(part))

        token_to_attrs[split_token_in_parts(ttype)] = attrs, important

    return _StyleFromDict(token_to_attrs)


class _StyleFromDict(Style):
    """
    Turn a dictionary that maps `Token` to `Attrs` into a style class.

    The algorithm is as follows.
    - If a given element has the ``Token.A.B.C|Token.X.Y.Z`` tokens.
      then we first look whether there is a style given for ABC|XYZ, if not,
      then we walk through all the parents. These are AB|XYZ and ABC|XY. We check
      whether a style for any of the parents was given.

    :param token_to_attrs: Dictionary that maps `Token` to `Attrs`.
    """
    def __init__(self, token_to_attrs):
        self.token_to_attrs = token_to_attrs

    def get_attrs_for_token(self, token):
        """
        Get `Attrs` for the given token.
        """
        # Split Token.
        # `token` can look like: ('Dialog', ':', 'Frame': 'Scrollbar', 'Button')
        # The split operation will split on the ':' parts.
        parts = split_token_in_parts(token)
        parts = tuple(sorted(parts))

        # For each part, list all prefixes.
        # E.g. ('Scrollbar', 'Button') will become
        #     (), ('Scrollbar', ) and ('Scrollbar', 'Button')
        def get_possibilte_prefixes(part):
            result = []
            for i in range(len(part) + 1):
                result.append(part[:i])
            return result
        possible_part_prefixes = [
                get_possibilte_prefixes(p) for p in parts]

        # Take the product of all possible prefixes.
        combos = []
        for comb in itertools.product(*possible_part_prefixes):
            # (Exclude the empty parts.)
            combos.append(tuple(sorted(p for p in comb if p)))

        # Always include default style.
        combos.append( () )

        # Order them according to their importance. More precise matches get
        # higher priority.
        def flattened_len(items):
            return sum(map(len, items))

        combos = sorted(combos, key=flattened_len)

        # Get list of Attrs, according to matches in our Style, along with
        # their importance.
        list_of_attrs_and_importance = [(DEFAULT_ATTRS, False)]

        for combo in combos:
            try:
                attrs_and_importance = self.token_to_attrs[combo]
            except KeyError:
                pass
            else:
                list_of_attrs_and_importance.append(attrs_and_importance)

        # Sort the Attrs objects that we have according to their importance.
        # This is a stable sort, so the order won't change for things that have
        # the same priority.
        list_of_attrs = [a[0] for a in sorted(list_of_attrs_and_importance, key=lambda a: a[1])]

        return merge_attrs(list_of_attrs)

    def invalidation_hash(self):
        return id(self.token_to_attrs)
