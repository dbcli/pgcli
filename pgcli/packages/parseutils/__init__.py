import sqlparse


def query_starts_with(query, prefixes):
    """Check if the query starts with any item from *prefixes*."""
    prefixes = [prefix.lower() for prefix in prefixes]
    formatted_sql = sqlparse.format(query.lower(), strip_comments=True).strip()
    return bool(formatted_sql) and formatted_sql.split()[0] in prefixes


def queries_start_with(queries, prefixes):
    """Check if any queries start with any item from *prefixes*."""
    for query in sqlparse.split(queries):
        if query and query_starts_with(query, prefixes) is True:
            return True
    return False


def is_destructive(queries):
    """Returns if any of the queries in *queries* is destructive."""
    keywords = ("drop", "shutdown", "delete", "truncate", "alter")
    return queries_start_with(queries, keywords)
