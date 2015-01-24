import logging
import psycopg2
import psycopg2.extras
import psycopg2.extensions
import sqlparse
from pandas import DataFrame
from .packages import pgspecial

_logger = logging.getLogger(__name__)

# Cast all database input to unicode automatically.
# See http://initd.org/psycopg/docs/usage.html#unicode-handling for more info.
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

# Cast bytea fields to text. By default, this will render as hex strings with
# Postgres 9+ and as escaped binary in earlier versions.
psycopg2.extensions.register_type(
    psycopg2.extensions.new_type((17,), 'BYTEA_TEXT', psycopg2.STRING))

# When running a query, make pressing CTRL+C raise a KeyboardInterrupt
# See http://initd.org/psycopg/articles/2014/07/20/cancelling-postgresql-statements-python/
psycopg2.extensions.set_wait_callback(psycopg2.extras.wait_select)

class PGExecute(object):

    schemata_query = '''
        SELECT  nspname
        FROM    pg_catalog.pg_namespace
        WHERE   nspname !~ '^pg_'
                AND nspname <> 'information_schema' '''

    tables_query = '''
        SELECT 	n.nspname schema_name,
                c.relname table_name,
                pg_catalog.pg_table_is_visible(c.oid) is_visible
        FROM 	pg_catalog.pg_class c
                LEFT JOIN pg_catalog.pg_namespace n
                    ON n.oid = c.relnamespace
        WHERE 	c.relkind IN ('r','v', 'm') -- table, view, materialized view
                AND n.nspname !~ '^pg_toast'
                AND n.nspname NOT IN ('information_schema', 'pg_catalog')
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
        conn = psycopg2.connect(database=database or self.dbname, user=user or
                self.user, password=password or self.password, host=host or
                self.host, port=port or self.port)
        if hasattr(self, 'conn'):
            self.conn.close()
        self.conn = conn
        self.conn.autocommit = True

    def run(self, sql):
        """Execute the sql in the database and return the results. The results
        are a list of tuples. Each tuple has 3 values (rows, headers, status).
        """

        # Remove spaces and EOL
        sql = sql.strip()
        if not sql:  # Empty string
            return [(None, None, None)]

        # Remove spaces, eol and semi-colons.
        sql = sql.rstrip(';')

        # Check if the command is a \c or 'use'. This is a special exception
        # that cannot be offloaded to `pgspecial` lib. Because we have to
        # change the database connection that we're connected to.
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
            return [(None, None, 'You are now connected to database "%s" as '
                    'user "%s"' % (self.dbname, self.user))]

        try:   # Special command
            _logger.debug('Trying a pgspecial command. sql: %r', sql)
            cur = self.conn.cursor()
            return pgspecial.execute(cur, sql)
        except KeyError:  # Regular SQL
            # Split the sql into separate queries and run each one. If any
            # single query fails, the rest of them are not run and no results
            # are shown.
            queries = sqlparse.split(sql)
            return [self.execute_normal_sql(query) for query in queries]

    def execute_normal_sql(self, split_sql):
        _logger.debug('Regular sql statement. sql: %r', split_sql)
        cur = self.conn.cursor()
        cur.execute(split_sql)
        # cur.description will be None for operations that do not return
        # rows.
        if cur.description:
            headers = [x[0] for x in cur.description]
            return (cur, headers, cur.statusmessage)
        else:
            _logger.debug('No rows in result.')
            return (None, None, cur.statusmessage)

    def get_metadata(self):
        """ Returns a tuple [schemata, tables, columns] of DataFrames

            schemata:   DataFrame with columns [schema]
            tables:     DataFrame with columns [schema, table, is_visible]
            columns:    DataFrame with columns [schema, table, column]

        """

        with self.conn.cursor() as cur:
            _logger.debug('Schemata Query. sql: %r', self.schemata_query)
            cur.execute(self.schemata_query)
            schemata = DataFrame.from_records(cur,
                        columns=['schema'])

        with self.conn.cursor() as cur:
            _logger.debug('Tables Query. sql: %r', self.tables_query)
            cur.execute(self.tables_query)
            tables = DataFrame.from_records(cur,
                      columns=['schema', 'table', 'is_visible'])

        with self.conn.cursor() as cur:
            _logger.debug('Columns Query. sql: %r', self.columns_query)
            cur.execute(self.columns_query)
            columns = DataFrame.from_records(cur,
                        columns=['schema', 'table', 'column'])

        return [schemata, tables, columns]

    def databases(self):
        with self.conn.cursor() as cur:
            _logger.debug('Databases Query. sql: %r', self.databases_query)
            cur.execute(self.databases_query)
            return [x[0] for x in cur.fetchall()]
