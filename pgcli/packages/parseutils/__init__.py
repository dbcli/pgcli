import sqlparse

sqlparse.engine.grouping.MAX_GROUPING_DEPTH = None
sqlparse.engine.grouping.MAX_GROUPING_TOKENS = None

BASE_KEYWORDS = [
    "drop",
    "shutdown",
    "delete",
    "truncate",
    "alter",
    "unconditional_update",
]
ALL_KEYWORDS = BASE_KEYWORDS + ["update"]


def query_starts_with(formatted_sql, prefixes):
    """Check if the query starts with any item from *prefixes*."""
    prefixes = [prefix.lower() for prefix in prefixes]
    return bool(formatted_sql) and formatted_sql.split()[0] in prefixes


def query_is_unconditional_update(query):
    """Check if the query starts with UPDATE and contains no top-level WHERE clause.

    Uses sqlparse's parse tree (rather than naive whitespace splitting) so that
    the word "where" appearing inside a string literal, comment, or a nested
    subquery doesn't get mistaken for an actual WHERE clause.
    """
    statements = sqlparse.parse(query)
    if not statements:
        return False
    statement = statements[0]

    first_token = statement.token_first(skip_cm=True)
    if first_token is None or first_token.ttype is not sqlparse.tokens.DML:
        return False
    if first_token.value.upper() != "UPDATE":
        return False

    return not any(isinstance(token, sqlparse.sql.Where) for token in statement.tokens)


def is_destructive(queries, keywords):
    """Returns if any of the queries in *queries* is destructive."""
    for query in sqlparse.split(queries):
        if query:
            formatted_sql = sqlparse.format(query.lower(), strip_comments=True).strip()
            if "unconditional_update" in keywords and query_is_unconditional_update(query):
                return True
            if query_starts_with(formatted_sql, keywords):
                return True
    return False


def parse_destructive_warning(warning_level):
    """Converts a deprecated destructive warning option to a list of command keywords."""
    if not warning_level:
        return []

    if not isinstance(warning_level, list):
        if "," in warning_level:
            return warning_level.split(",")
        warning_level = [warning_level]

    return {
        "true": ALL_KEYWORDS,
        "false": [],
        "all": ALL_KEYWORDS,
        "moderate": BASE_KEYWORDS,
        "off": [],
        "": [],
    }.get(warning_level[0], warning_level)
