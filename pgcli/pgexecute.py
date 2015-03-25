import logging
import psycopg2
import psycopg2.extras
import psycopg2.extensions as ext
import sqlparse
from .packages import pgspecial
from .encodingutils import unicode2utf8

_logger = logging.getLogger(__name__)

# Cast all database input to unicode automatically.
# See http://initd.org/psycopg/docs/usage.html#unicode-handling for more info.
ext.register_type(ext.UNICODE)
ext.register_type(ext.UNICODEARRAY)
ext.register_type(ext.new_type((705,), "UNKNOWN", ext.UNICODE))

# Cast bytea fields to text. By default, this will render as hex strings with
# Postgres 9+ and as escaped binary in earlier versions.
ext.register_type(ext.new_type((17,), 'BYTEA_TEXT', psycopg2.STRING))

# When running a query, make pressing CTRL+C raise a KeyboardInterrupt
# See http://initd.org/psycopg/articles/2014/07/20/cancelling-postgresql-statements-python/
ext.set_wait_callback(psycopg2.extras.wait_select)


def register_json_typecasters(conn, loads_fn):
    """Set the function for converting JSON data for a connection.

    Use the supplied function to decode JSON data returned from the database
    via the given connection. The function should accept a single argument of
    the data as a string encoded in the database's character encoding.
    psycopg2's default handler for JSON data is json.loads.
    http://initd.org/psycopg/docs/extras.html#json-adaptation

    This function attempts to register the typecaster for both JSON and JSONB
    types.

    Returns a set that is a subset of {'json', 'jsonb'} indicating which types
    (if any) were successfully registered.
    """
    available = set()

    for name in ['json', 'jsonb']:
        try:
            psycopg2.extras.register_json(conn, loads=loads_fn, name=name)
            available.add(name)
        except psycopg2.ProgrammingError:
            pass

    return available

def register_hstore_typecaster(conn):
    """
    Instead of using register_hstore() which converts hstore into a python
    dict, we query the 'oid' of hstore which will be different for each
    database and register a type caster that converts it to unicode.
    http://initd.org/psycopg/docs/extras.html#psycopg2.extras.register_hstore
    """
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT 'hstore'::regtype::oid")
            oid = cur.fetchone()[0]
            ext.register_type(ext.new_type((oid,), "HSTORE", ext.UNICODE))
        except Exception:
            pass

class PGExecute(object):

    search_path_query = '''
        SELECT * FROM unnest(current_schemas(false))'''

    schemata_query = '''
        SELECT  nspname
        FROM    pg_catalog.pg_namespace
        WHERE   nspname !~ '^pg_'
                AND nspname <> 'information_schema'
        ORDER BY 1 '''

    tables_query = '''
        SELECT 	n.nspname schema_name,
                c.relname table_name
        FROM 	pg_catalog.pg_class c
                LEFT JOIN pg_catalog.pg_namespace n
                    ON n.oid = c.relnamespace
        WHERE 	c.relkind IN ('r','v', 'm') -- table, view, materialized view
                AND n.nspname !~ '^pg_'
                AND nspname <> 'information_schema'
        ORDER BY 1,2;'''

    columns_query = '''
        SELECT 	nsp.nspname schema_name,
                cls.relname table_name,
                att.attname column_name
        FROM 	pg_catalog.pg_attribute att
                INNER JOIN pg_catalog.pg_class cls
                    ON att.attrelid = cls.oid
                INNER JOIN pg_catalog.pg_namespace nsp
                    ON cls.relnamespace = nsp.oid
        WHERE 	cls.relkind IN ('r', 'v', 'm')
                AND nsp.nspname !~ '^pg_'
                AND nsp.nspname <> 'information_schema'
                AND NOT att.attisdropped
                AND att.attnum  > 0
        ORDER BY 1, 2, 3'''

    functions_query = '''
        SELECT 	DISTINCT  --multiple dispatch means possible duplicates
                n.nspname schema_name,
                p.proname func_name
        FROM 	pg_catalog.pg_proc p
                INNER JOIN pg_catalog.pg_namespace n
                    ON n.oid = p.pronamespace
        WHERE 	n.nspname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY 1, 2'''


    databases_query = """SELECT d.datname as "Name",
       pg_catalog.pg_get_userbyid(d.datdba) as "Owner",
       pg_catalog.pg_encoding_to_char(d.encoding) as "Encoding",
       d.datcollate as "Collate",
       d.datctype as "Ctype",
       pg_catalog.array_to_string(d.datacl, E'\n') AS "Access privileges"
    FROM pg_catalog.pg_database d
    ORDER BY 1;"""

    def __init__(self, database, user, password, host, port):
        self.dbname = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connect()

    def connect(self, database=None, user=None, password=None, host=None,
            port=None):

        db = unicode2utf8(database or self.dbname)
        user = unicode2utf8(user or self.user)
        password = unicode2utf8(password or self.password)
        host = unicode2utf8(host or self.host)
        port = unicode2utf8(port or self.port)
        conn = psycopg2.connect(database=db, user=user, password=password,
                host=host, port=port)
        if hasattr(self, 'conn'):
            self.conn.close()
        self.conn = conn
        self.conn.autocommit = True
        register_json_typecasters(self.conn, self._json_typecaster)
        register_hstore_typecaster(self.conn)

    def _json_typecaster(self, json_data):
        """Interpret incoming JSON data as a string.

        The raw data is decoded using the connection's encoding, which defaults
        to the database's encoding.

        See http://initd.org/psycopg/docs/connection.html#connection.encoding
        """

        return json_data.decode(self.conn.encoding)

    def run(self, statement):
        """Execute the sql in the database and return the results. The results
        are a list of tuples. Each tuple has 3 values (rows, headers, status).
        """

        # Remove spaces and EOL
        statement = statement.strip()
        if not statement:  # Empty string
            yield (None, None, None, None)

        # Split the sql into separate queries and run each one.
        for sql in sqlparse.split(statement):
            # Remove spaces, eol and semi-colons.
            sql = sql.rstrip(';')

            # Check if the command is a \c or 'use'. This is a special
            # exception that cannot be offloaded to `pgspecial` lib. Because we
            # have to change the database connection that we're connected to.
            if sql.startswith('\c') or sql.lower().startswith('use'):
                _logger.debug('Database change command detected.')
                try:
                    dbname = sql.split()[1]
                except:
                    _logger.debug('Database name missing.')
                    raise RuntimeError('Database name missing.')
                self.connect(database=dbname)
                self.dbname = dbname
                _logger.debug('Successfully switched to DB: %r', dbname)
                yield (None, None, None, 'You are now connected to database "%s" as '
                        'user "%s"' % (self.dbname, self.user))
            else:
                try:   # Special command
                    _logger.debug('Trying a pgspecial command. sql: %r', sql)
                    cur = self.conn.cursor()
                    for result in pgspecial.execute(cur, sql):
                        yield result
                except KeyError:  # Regular SQL
                    yield self.execute_normal_sql(sql)

    def execute_normal_sql(self, split_sql):
        _logger.debug('Regular sql statement. sql: %r', split_sql)
        cur = self.conn.cursor()
        cur.execute(split_sql)
        try:
            title = self.conn.notices.pop()
        except IndexError:
            title = None
        # cur.description will be None for operations that do not return
        # rows.
        if cur.description:
            headers = [x[0] for x in cur.description]
            return (title, cur, headers, cur.statusmessage)
        else:
            _logger.debug('No rows in result.')
            return (title, None, None, cur.statusmessage)

    def search_path(self):
        """Returns the current search path as a list of schema names"""

        with self.conn.cursor() as cur:
            _logger.debug('Search path query. sql: %r', self.search_path_query)
            cur.execute(self.search_path_query)
            return [x[0] for x in cur.fetchall()]

    def schemata(self):
        """Returns a list of schema names in the database"""

        with self.conn.cursor() as cur:
            _logger.debug('Schemata Query. sql: %r', self.schemata_query)
            cur.execute(self.schemata_query)
            return [x[0] for x in cur.fetchall()]

    def tables(self):
        """Returns a list of (schema_name, table_name) tuples """

        with self.conn.cursor() as cur:
            _logger.debug('Tables Query. sql: %r', self.tables_query)
            cur.execute(self.tables_query)
            return cur.fetchall()

    def columns(self):
        """Returns a list of (schema_name, table_name, column_name) tuples"""

        with self.conn.cursor() as cur:
            _logger.debug('Columns Query. sql: %r', self.columns_query)
            cur.execute(self.columns_query)
            return cur.fetchall()

    def databases(self):
        with self.conn.cursor() as cur:
            _logger.debug('Databases Query. sql: %r', self.databases_query)
            cur.execute(self.databases_query)
            return [x[0] for x in cur.fetchall()]

    def functions(self):
        """Yields tuples of (schema_name, function_name)"""

        with self.conn.cursor() as cur:
            _logger.debug('Functions Query. sql: %r', self.functions_query)
            cur.execute(self.functions_query)
            for row in cur:
                yield row
