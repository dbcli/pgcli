import sqlparse


def query_starts_with(formatted_sql, prefixes):
    """Check if the query starts with any item from *prefixes*."""
    prefixes = [prefix.lower() for prefix in prefixes]
    return bool(formatted_sql) and formatted_sql.split()[0] in prefixes


def query_is_unconditional_update(formatted_sql):
    """Check if the query starts with UPDATE and contains no WHERE."""
    tokens = formatted_sql.split()
    return bool(tokens) and tokens[0] == "update" and "where" not in tokens


def query_is_simple_update(formatted_sql):
    """Check if the query starts with UPDATE."""
    tokens = formatted_sql.split()
    return bool(tokens) and tokens[0] == "update"


def is_destructive(queries, warning_level="all"):
    """Returns if any of the queries in *queries* is destructive."""
    keywords = ("drop", "shutdown", "delete", "truncate", "alter")
    for query in sqlparse.split(queries):
        if query:
            formatted_sql = sqlparse.format(query.lower(), strip_comments=True).strip()
            if query_starts_with(formatted_sql, keywords):
                return True
            if query_is_unconditional_update(formatted_sql):
                return True
            if warning_level == "all" and query_is_simple_update(formatted_sql):
                return True
    return False
