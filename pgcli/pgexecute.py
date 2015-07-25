import logging
import psycopg2
import psycopg2.extras
import psycopg2.extensions as ext
import sqlparse
from .packages import pgspecial as special
from .encodingutils import unicode2utf8, PY2

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

    # The boolean argument to the current_schemas function indicates whether
    # implicit schemas, e.g. pg_catalog
    search_path_query = '''
        SELECT * FROM unnest(current_schemas(true))'''

    schemata_query = '''
        SELECT  nspname
        FROM    pg_catalog.pg_namespace
        ORDER BY 1 '''

    tables_query = '''
        SELECT 	n.nspname schema_name,
                c.relname table_name
        FROM 	pg_catalog.pg_class c
                LEFT JOIN pg_catalog.pg_namespace n
                    ON n.oid = c.relnamespace
        WHERE 	c.relkind = ANY(%s)
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
        WHERE 	cls.relkind = ANY(%s)
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

    datatypes_query = '''
        SELECT n.nspname schema_name,
               t.typname type_name
        FROM   pg_catalog.pg_type t
               INNER JOIN pg_catalog.pg_namespace n
                  ON n.oid = t.typnamespace
        WHERE ( t.typrelid = 0  -- non-composite types
                OR (  -- composite type, but not a table
                      SELECT c.relkind = 'c'
                      FROM pg_catalog.pg_class c
                      WHERE c.oid = t.typrelid
                    )
              )
              AND NOT EXISTS( -- ignore array types
                    SELECT  1
                    FROM    pg_catalog.pg_type el
                    WHERE   el.oid = t.typelem AND el.typarray = t.oid
                  )
              AND n.nspname <> 'pg_catalog'
              AND n.nspname <> 'information_schema'
        ORDER BY 1, 2;'''

    def __init__(self, database, user, password, host, port):
        self.dbname = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connect()

    def connect(self, database=None, user=None, password=None, host=None,
            port=None):

        db = (database or self.dbname)
        user = (user or self.user)
        password = (password or self.password)
        host = (host or self.host)
        port = (port or self.port)
        conn = psycopg2.connect(
                database=unicode2utf8(db),
                user=unicode2utf8(user),
                password=unicode2utf8(password),
                host=unicode2utf8(host),
                port=unicode2utf8(port))
        conn.set_client_encoding('utf8')
        if hasattr(self, 'conn'):
            self.conn.close()
        self.conn = conn
        self.conn.autocommit = True
        self.dbname = db
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        register_json_typecasters(self.conn, self._json_typecaster)
        register_hstore_typecaster(self.conn)

    def _json_typecaster(self, json_data):
        """Interpret incoming JSON data as a string.

        The raw data is decoded using the connection's encoding, which defaults
        to the database's encoding.

        See http://initd.org/psycopg/docs/connection.html#connection.encoding
        """

        if PY2:
            return json_data.decode(self.conn.encoding)
        else:
            return json_data

    def run(self, statement, pgspecial=None):
        """Execute the sql in the database and return the results.

        :param statement: A string containing one or more sql statements
        :param pgspecial: PGSpecial object
        :return: List of tuples containing (title, rows, headers, status)
        """

        # Remove spaces and EOL
        statement = statement.strip()
        if not statement:  # Empty string
            yield (None, None, None, None)

        # Split the sql into separate queries and run each one.
        for sql in sqlparse.split(statement):
            # Remove spaces, eol and semi-colons.
            sql = sql.rstrip(';')

            if pgspecial:
                # First try to run each query as special
                try:
                    _logger.debug('Trying a pgspecial command. sql: %r', sql)
                    cur = self.conn.cursor()
                    for result in pgspecial.execute(cur, sql):
                        yield result
                    return
                except special.CommandNotFound:
                    pass

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

    def _relations(self, kinds=('r', 'v', 'm')):
        """Get table or view name metadata

        :param kinds: list of postgres relkind filters:
                'r' - table
                'v' - view
                'm' - materialized view
        :return: (schema_name, rel_name) tuples
        """

        with self.conn.cursor() as cur:
            sql = cur.mogrify(self.tables_query, [kinds])
            _logger.debug('Tables Query. sql: %r', sql)
            cur.execute(sql)
            for row in cur:
                yield row

    def tables(self):
        """Yields (schema_name, table_name) tuples"""
        for row in self._relations(kinds=['r']):
            yield row

    def views(self):
        """Yields (schema_name, view_name) tuples.

            Includes both views and and materialized views
        """
        for row in self._relations(kinds=['v', 'm']):
            yield row

    def _columns(self, kinds=('r', 'v', 'm')):
        """Get column metadata for tables and views

        :param kinds: kinds: list of postgres relkind filters:
                'r' - table
                'v' - view
                'm' - materialized view
        :return: list of (schema_name, relation_name, column_name) tuples
        """

        with self.conn.cursor() as cur:
            sql = cur.mogrify(self.columns_query, [kinds])
            _logger.debug('Columns Query. sql: %r', sql)
            cur.execute(sql)
            for row in cur:
                yield row

    def table_columns(self):
        for row in self._columns(kinds=['r']):
            yield row

    def view_columns(self):
        for row in self._columns(kinds=['v', 'm']):
            yield row

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

    def datatypes(self):
        """Yields tuples of (schema_name, type_name)"""

        with self.conn.cursor() as cur:
            _logger.debug('Datatypes Query. sql: %r', self.datatypes_query)
            cur.execute(self.datatypes_query)
            for row in cur:
                yield row
