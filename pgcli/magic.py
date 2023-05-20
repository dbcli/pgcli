from .main import PGCli
import sql.parse
import sql.connection
import logging

_logger = logging.getLogger(__name__)


def load_ipython_extension(ipython):
    """This is called via the ipython command '%load_ext pgcli.magic'"""

    # first, load the sql magic if it isn't already loaded
    if not ipython.find_line_magic("sql"):
        ipython.run_line_magic("load_ext", "sql")

    # register our own magic
    ipython.register_magic_function(pgcli_line_magic, "line", "pgcli")


def pgcli_line_magic(line):
    _logger.debug("pgcli magic called: %r", line)
    parsed = sql.parse.parse(line, {})
    # "get" was renamed to "set" in ipython-sql:
    # https://github.com/catherinedevlin/ipython-sql/commit/f4283c65aaf68f961e84019e8b939e4a3c501d43
    if hasattr(sql.connection.Connection, "get"):
        conn = sql.connection.Connection.get(parsed["connection"])
    else:
        try:
            conn = sql.connection.Connection.set(parsed["connection"])
        # a new positional argument was added to Connection.set in version 0.4.0 of ipython-sql
        except TypeError:
            conn = sql.connection.Connection.set(parsed["connection"], False)

    try:
        # A corresponding pgcli object already exists
        pgcli = conn._pgcli
        _logger.debug("Reusing existing pgcli")
    except AttributeError:
        # I can't figure out how to get the underylying psycopg2 connection
        # from the sqlalchemy connection, so just grab the url and make a
        # new connection
        pgcli = PGCli()
        u = conn.session.engine.url
        _logger.debug("New pgcli: %r", str(u))

        pgcli.connect_uri(str(u._replace(drivername="postgres")))
        conn._pgcli = pgcli

    # For convenience, print the connection alias
    print(f"Connected: {conn.name}")

    try:
        pgcli.run_cli()
    except SystemExit:
        pass

    if not pgcli.query_history:
        return

    q = pgcli.query_history[-1]

    if not q.successful:
        _logger.debug("Unsuccessful query - ignoring")
        return

    if q.meta_changed or q.db_changed or q.path_changed:
        _logger.debug("Dangerous query detected -- ignoring")
        return

    ipython = get_ipython()
    return ipython.run_cell_magic("sql", line, q.query)
