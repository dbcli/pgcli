r"""psql's \crosstabview: show a query result as a crosstab (pivot) grid.

The rules and error messages follow psql's crosstabview.c.
"""

import re

# psql's CROSSTABVIEW_MAX_COLUMNS
MAX_COLUMNS = 1600

# "<query> \crosstabview [args]". An arg is a word or a "quoted" name; a single
# quote in the tail means the \crosstabview is inside a string literal.
_TERMINATOR = re.compile(r'^(.*?)\s*\\crosstabview((?:\s+(?:"[^"]*"|[^\s"\'])+)*)\s*$', re.DOTALL)


class CrosstabViewError(Exception):
    pass


def split_query(sql):
    r"""Split "<query> \crosstabview [args]" into (query, args), or None."""
    match = _TERMINATOR.match(sql)
    if match is None:
        return None
    return match.group(1), match.group(2)


def parse_args(text):
    """Split the arguments on whitespace, keeping "quoted" names whole."""
    return re.findall(r'(?:"[^"]*"|[^\s"])+', text or "")


def _dequote_downcase(arg):
    """Like psql: downcase unquoted letters, strip quotes, "" means "."""
    out = []
    quoted = False
    i = 0
    while i < len(arg):
        c = arg[i]
        if c == '"':
            if quoted and arg[i + 1 : i + 2] == '"':
                out.append('"')
                i += 1
            else:
                quoted = not quoted
        else:
            out.append(c if quoted or not "A" <= c <= "Z" else c.lower())
        i += 1
    return "".join(out)


def _column_index(arg, headers):
    """Resolve a column given by number (1-based) or by name."""
    if arg.isdigit() and arg.isascii():
        idx = int(arg) - 1
        if not 0 <= idx < len(headers):
            raise CrosstabViewError(f"\\crosstabview: column number {idx + 1} is out of range 1..{len(headers)}")
        return idx
    name = _dequote_downcase(arg)
    matches = [i for i, header in enumerate(headers) if header == name]
    if len(matches) > 1:
        raise CrosstabViewError(f'\\crosstabview: ambiguous column name: "{name}"')
    if not matches:
        raise CrosstabViewError(f'\\crosstabview: column name not found: "{name}"')
    return matches[0]


def _key(value):
    # psql compares the text of the values; NULL is a value of its own.
    return None if value is None else str(value)


def _rank(value):
    # A sort value counts only when it is an integer; anything else ranks 0.
    text = _key(value)
    return int(text) if text is not None and re.fullmatch(r"-?[0-9]+", text) else 0


def crosstabview(headers, rows, args):
    """Pivot rows like psql's \\crosstabview colV colH [colD [sortcolH]].

    Returns (rows, headers). A NULL horizontal header is returned as None;
    cells with no data value are empty strings.
    """
    if len(headers) < 3:
        raise CrosstabViewError("\\crosstabview: query must return at least three columns")
    args = list(args[:4]) + [None] * (4 - len(args[:4]))

    col_v = 0 if args[0] is None else _column_index(args[0], headers)
    col_h = 1 if args[1] is None else _column_index(args[1], headers)
    if col_v == col_h:
        raise CrosstabViewError("\\crosstabview: vertical and horizontal headers must be different columns")
    if args[2] is None:
        if len(headers) != 3:
            raise CrosstabViewError("\\crosstabview: data column must be specified when query returns more than three columns")
        col_d = 3 - col_v - col_h  # the column that is left
    else:
        col_d = _column_index(args[2], headers)
    col_sort = None if args[3] is None else _column_index(args[3], headers)

    # Distinct header values, in order of first appearance.
    h_ranks = {}
    v_labels = {}
    for row in rows:
        h = _key(row[col_h])
        if h not in h_ranks:
            h_ranks[h] = 0 if col_sort is None else _rank(row[col_sort])
            if len(h_ranks) > MAX_COLUMNS:
                raise CrosstabViewError(f"\\crosstabview: maximum number of columns ({MAX_COLUMNS}) exceeded")
        v_labels.setdefault(_key(row[col_v]), row[col_v])

    h_order = list(h_ranks)
    if col_sort is not None:
        # Sort by rank; ties are in name order (NULL last), as in psql.
        h_order.sort(key=lambda h: (h is None, h or ""))
        h_order.sort(key=h_ranks.get)
    h_index = {h: i for i, h in enumerate(h_order, 1)}
    v_index = {v: i for i, v in enumerate(v_labels)}

    empty = object()
    grid = [[label] + [empty] * len(h_order) for label in v_labels.values()]
    for row in rows:
        v, h = _key(row[col_v]), _key(row[col_h])
        cells = grid[v_index[v]]
        if cells[h_index[h]] is not empty:
            raise CrosstabViewError(
                f'\\crosstabview: query result contains multiple data values for row "{"(null)" if v is None else v}", '
                f'column "{"(null)" if h is None else h}"'
            )
        cells[h_index[h]] = row[col_d]

    grid = [[("" if cell is empty else cell) for cell in cells] for cells in grid]
    return grid, [headers[col_v]] + h_order
