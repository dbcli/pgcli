"""
This is an implementation of wcwidth() and wcswidth() (defined in
IEEE Std 1002.1-2001) for Unicode.

https://github.com/jquast/wcwidth
"""
# from Markus Kuhn's C code at:
#
#     http://www.cl.cam.ac.uk/~mgk25/ucs/wcwidth.c
#
# This is an implementation of wcwidth() and wcswidth() (defined in
# IEEE Std 1002.1-2001) for Unicode.
#
# http://www.opengroup.org/onlinepubs/007904975/functions/wcwidth.html
# http://www.opengroup.org/onlinepubs/007904975/functions/wcswidth.html
#
# In fixed-width output devices, Latin characters all occupy a single
# "cell" position of equal width, whereas ideographic CJK characters
# occupy two such cells. Interoperability between terminal-line
# applications and (teletype-style) character terminals using the
# UTF-8 encoding requires agreement on which character should advance
# the cursor by how many cell positions. No established formal
# standards exist at present on which Unicode character shall occupy
# how many cell positions on character terminals. These routines are
# a first attempt of defining such behavior based on simple rules
# applied to data provided by the Unicode Consortium.
#
# For some graphical characters, the Unicode standard explicitly
# defines a character-cell width via the definition of the East Asian
# FullWidth (F), Wide (W), Half-width (H), and Narrow (Na) classes.
# In all these cases, there is no ambiguity about which width a
# terminal shall use. For characters in the East Asian Ambiguous (A)
# class, the width choice depends purely on a preference of backward
# compatibility with either historic CJK or Western practice.
# Choosing single-width for these characters is easy to justify as
# the appropriate long-term solution, as the CJK practice of
# displaying these characters as double-width comes from historic
# implementation simplicity (8-bit encoded characters were displayed
# single-width and 16-bit ones double-width, even for Greek,
# Cyrillic, etc.) and not any typographic considerations.
#
# Much less clear is the choice of width for the Not East Asian
# (Neutral) class. Existing practice does not dictate a width for any
# of these characters. It would nevertheless make sense
# typographically to allocate two character cells to characters such
# as for instance EM SPACE or VOLUME INTEGRAL, which cannot be
# represented adequately with a single-width glyph. The following
# routines at present merely assign a single-cell width to all
# neutral characters, in the interest of simplicity. This is not
# entirely satisfactory and should be reconsidered before
# establishing a formal standard in this area. At the moment, the
# decision which Not East Asian (Neutral) characters should be
# represented by double-width glyphs cannot yet be answered by
# applying a simple rule from the Unicode database content. Setting
# up a proper standard for the behavior of UTF-8 character terminals
# will require a careful analysis not only of each Unicode character,
# but also of each presentation form, something the author of these
# routines has avoided to do so far.
#
# http://www.unicode.org/unicode/reports/tr11/
#
# Markus Kuhn -- 2007-05-26 (Unicode 5.0)
#
# Permission to use, copy, modify, and distribute this software
# for any purpose and without fee is hereby granted. The author
# disclaims all warranties with regard to this software.
#
# Latest version: http://www.cl.cam.ac.uk/~mgk25/ucs/wcwidth.c

from __future__ import division
from .table_wide import WIDE_EASTASIAN
from .table_comb import NONZERO_COMBINING


def _bisearch(ucs, table):
    " auxiliary function for binary search in interval table "
    lbound = 0
    ubound = len(table) - 1

    if ucs < table[0][0] or ucs > table[ubound][1]:
        return 0
    while ubound >= lbound:
        mid = (lbound + ubound) // 2
        if ucs > table[mid][1]:
            lbound = mid + 1
        elif ucs < table[mid][0]:
            ubound = mid - 1
        else:
            return 1

    return 0


def wcwidth(wc):
    """wcwidth(wc) -> int

    The wcwidth() function returns 0 if the wc argument has no printable effect
    on a terminal (such as NUL '\0'), -1 if wc is not printable, or has an
    indeterminate effect on the terminal (control or combining).  Otherwise,
    the number of column positions the character occupies on a graphic terminal
    (1 or 2).

    The following have a column width of -1:

        - Non-spacing and enclosing combining characters (general
          category code Mn or Me in the Unicode database). Generally,
          having a non-zero value returned by ``unicodedata.combining()``.

        - C0 control characters (U+001 through U+01F).

        - C1 control characters and DEL (U+07F through U+0A0).

    The following have a column width of 0:

        - NULL (U+0000, 0).

        - COMBINING GRAPHEME JOINER (U+034F).

        - ZERO WIDTH SPACE (U+200B) through
          RIGHT-TO-LEFT MARK (U+200F).

        - LINE SEPERATOR (U+2028) and
          PARAGRAPH SEPERATOR (U+2029).

        - LEFT-TO-RIGHT EMBEDDING (U+202A) through
          RIGHT-TO-LEFT OVERRIDE (U+202E).

        - WORD JOINER (U+2060) through
          INVISIBLE SEPARATOR (U+2063).

    The following have a column width of 1:

        - SOFT HYPHEN (U+00AD) has a column width of 1.

        - All remaining characters (including all printable
          ISO 8859-1 and WGL4 characters, Unicode control characters,
          etc.) have a column width of 1.

    The following have a column width of 2:

        - Spacing characters in the East Asian Wide (W) or East Asian
          Full-width (F) category as defined in Unicode Technical
          Report #11 have a column width of 2.
    """
    ucs = ord(wc)

    # NOTE: created by hand, there isn't anything identifiable other than
    # general Cf category code to identify these, and some characters in Cf
    # category code are of non-zero width.
    if (0 == ucs or
            0x034F == ucs or
            0x200B <= ucs <= 0x200F or
            0x2028 == ucs or
            0x2029 == ucs or
            0x202A <= ucs <= 0x202E or
            0x2060 <= ucs <= 0x2063):
        return 0

    # C0/C1 control characters
    if ucs < 32 or 0x07F <= ucs < 0x0A0:
        return -1

    # combining characters have indeterminate effects unless
    # combined with additional characters.
    if _bisearch(ucs, NONZERO_COMBINING):
        return -1

    return 1 + _bisearch(ucs, WIDE_EASTASIAN)


def wcswidth(pwcs, n=None):

    """
    Return the width in character cells of the first ``n`` unicode string pwcs,
    or -1 if a  non-printable character is encountered. When ``n`` is None
    (default), return the length of the entire string.
    """

    end = len(pwcs) if n is not None else n
    idx = slice(0, end)
    width = 0
    for char in pwcs[idx]:
        wcw = wcwidth(char)
        if wcw < 0:
            return -1
        else:
            width += wcw
    return width
