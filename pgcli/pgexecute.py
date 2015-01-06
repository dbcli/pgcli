import logging
import psycopg2
import psycopg2.extensions
from .packages import pgspecial

_logger = logging.getLogger(__name__)

# Cast all database input to unicode automatically.
# See http://initd.org/psycopg/docs/usage.html#unicode-handling for more info.
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

def _parse_dsn(dsn, default_user, default_password, default_host,
        default_port):
    """
    This function parses a postgres url to get the different components.

    """

    user = password = host = port = dbname = None

    if dsn.startswith('postgres://'):  # Check if the string is a database url.
        dsn = dsn[len('postgres://'):]
    elif dsn.startswith('postgresql://'):
        dsn = dsn[len('postgresql://'):]

    if '/' in dsn:
        host, dbname = dsn.split('/', 1)
        if '@' in host:
            user, _, host = host.partition('@')
        if ':' in host:
            host, _, port = host.partition(':')
        if user and ':' in user:
            user, _, password = user.partition(':')

    user = user or default_user
    password = password or default_password
    host = host or default_host
    port = port or default_port
    dbname = dbname or dsn

    _logger.debug('Parsed connection params:'
            'dbname: %r, user: %r, password: %r, host: %r, port: %r',
            dbname, user, password, host, port)

    return (dbname, user, password, host, port)

class PGExecute(object):

    tables_query = '''SELECT c.relname as "Name" FROM pg_catalog.pg_class c
    LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE
    c.relkind IN ('r','') AND n.nspname <> 'pg_catalog' AND n.nspname <>
    'information_schema' AND n.nspname !~ '^pg_toast' AND
    pg_catalog.pg_table_is_visible(c.oid) ORDER BY 1;'''

    columns_query = '''SELECT column_name FROM information_schema.columns WHERE
    table_name =%s;'''

    databases_query = """SELECT d.datname as "Name",
       pg_catalog.pg_get_userbyid(d.datdba) as "Owner",
       pg_catalog.pg_encoding_to_char(d.encoding) as "Encoding",
       d.datcollate as "Collate",
       d.datctype as "Ctype",
       pg_catalog.array_to_string(d.datacl, E'\n') AS "Access privileges"
    FROM pg_catalog.pg_database d
    ORDER BY 1;"""

    def __init__(self, database, user, password, host, port):
        (self.dbname, self.user, self.password, self.host, self.port) = \
                _parse_dsn(database, default_user=user,
                        default_password=password, default_host=host,
                        default_port=port)
        self.conn = psycopg2.connect(database=self.dbname, user=self.user,
                password=self.password, host=self.host, port=self.port)
        self.conn.autocommit = True

    def run(self, sql):
        """Execute the sql in the database and return the results. The results
        are a list of tuples. Each tuple has 3 values (rows, headers, status).
        """

        if not sql:  # Empty string
            return [(None, None, None)]

        # Remove spaces, eol and semi-colons.
        sql = sql.strip()
        sql = sql.rstrip(';')

        # Check if the command is a \c or 'use'. This is a special exception
        # that cannot be offloaded to `pgspecial` lib. Because we have to
        # change the database connection that we're connected to.
        if sql.startswith('\c') or sql.lower().startswith('use'):
            _logger.debug('Database change command detected.')
            try:
                dbname = sql.split()[1]
            except:
                _logger.debug('Failed to switch. DB missing: %r', dbname)
                raise RuntimeError('Database name missing.')
            self.conn = psycopg2.connect(database=dbname,
                    user=self.user, password=self.password, host=self.host,
                    port=self.port)
            self.dbname = dbname
            self.conn.autocommit = True
            _logger.debug('Successfully switched to DB: %r', dbname)
            return [(None, None, 'You are now connected to database "%s" as '
                    'user "%s"' % (self.dbname, self.user))]

        with self.conn.cursor() as cur:
            try:
                _logger.debug('Trying a pgspecial command. sql: %r', sql)
                return pgspecial.execute(cur, sql)
            except KeyError:
                _logger.debug('Regular sql statement. sql: %r', sql)
                cur.execute(sql)

            # cur.description will be None for operations that do not return
            # rows.
            if cur.description:
                headers = [x[0] for x in cur.description]
                return [(cur.fetchall(), headers, cur.statusmessage)]
            else:
                _logger.debug('No rows in result.')
                return [(None, None, cur.statusmessage)]

    def tables(self):
        with self.conn.cursor() as cur:
            cur.execute(self.tables_query)
            return [x[0] for x in cur.fetchall()]

    def columns(self, table):
        with self.conn.cursor() as cur:
            cur.execute(self.columns_query, (table,))
            cols = [x[0] for x in cur.fetchall()]
            return cols

    def all_columns(self):
        columns = set()
        for table in self.tables():
            columns.update(self.columns(table))
        return columns

    def databases(self):
        with self.conn.cursor() as cur:
            cur.execute(self.databases_query)
            return [x[0] for x in cur.fetchall()]
