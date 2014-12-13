import psycopg2
from .packages import pgspecial

def _parse_dsn(dsn, default_user, default_password, default_host,
        default_port):
    """
    postgres://user:password@host:port/dbname
    postgres://user@host:port/dbname
    postgres://localhost:port/dbname
    postgres://user:password@host/dbname
    postgres://user@host/dbname
    postgres://localhost/dbname
    postgres:///dbname
    """

    user = password = host = port = dbname = None

    if '//' in dsn:  # Check if the string is a database url.
        # Assume that dsn starts with postgres://
        dsn = dsn.lstrip('postgres://')

        host, dbname = dsn.split('/', 1)
        if '@' in host:
            user, _, host = host.partition('@')
        if ':' in host:
            host, _, port = host.partition(':')
        if ':' in user:
            user, _, password = user.partition(':')

    user = user or default_user
    password = password or default_password
    host = host or default_host
    port = port or default_port
    dbname = dbname or dsn

    return (dbname, user, password, host, port)

class PGExecute(object):

    tables_query = '''SELECT c.relname as "Name" FROM pg_catalog.pg_class c
    LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE
    c.relkind IN ('r','') AND n.nspname <> 'pg_catalog' AND n.nspname <>
    'information_schema' AND n.nspname !~ '^pg_toast' AND
    pg_catalog.pg_table_is_visible(c.oid) ORDER BY 1;'''

    columns_query = '''SELECT column_name FROM information_schema.columns WHERE
    table_name =%s;'''

    databases_query = '''SELECT datname FROM pg_database;'''

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

        # Remove spaces, eol and semi-colons.
        sql = sql.strip()
        sql = sql.rstrip(';')

        # Check if the command is a \c or 'use'. This is a special exception
        # that cannot be offloaded to `pgspecial` lib. Because we have to
        # change the database connection that we're connected to.
        if sql.startswith('\c') or sql.lower().startswith('use'):
            try:
                dbname = sql.split()[1]
            except:
                raise RuntimeError('Database name missing.')
            self.conn = psycopg2.connect(database=dbname,
                    user=self.user, password=self.password, host=self.host,
                    port=self.port)
            self.dbname = dbname
            return [(None, None, 'You are now connected to database "%s" as '
                    'user "%s"' % (self.dbname, self.user))]

        with self.conn.cursor() as cur:
            try:
                return pgspecial.execute(cur, sql)
            except KeyError:
                cur.execute(sql)

            # cur.description will be None for operations that do not return
            # rows.
            if cur.description:
                headers = [x[0] for x in cur.description]
                return [(cur.fetchall(), headers, cur.statusmessage)]
            else:
                return [(None, None, cur.statusmessage)]

    def tables(self):
        with self.conn.cursor() as cur:
            cur.execute(self.tables_query)
            return [x[0] for x in cur.fetchall()]

    def columns(self, table):
        with self.conn.cursor() as cur:
            cur.execute(self.columns_query, (table,))
            return [x[0] for x in cur.fetchall()]

    def all_columns(self):
        columns = set()
        for table in self.tables():
            columns.update(self.columns(table))
        return columns

    def databases(self):
        with self.conn.cursor() as cur:
            cur.execute(self.databases_query)
            return [x[0] for x in cur.fetchall()]
