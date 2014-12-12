import psycopg2
from .packages import pgspecial

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
        self.conn = psycopg2.connect(database=database, user=user,
                password=password, host=host, port=port)
        self.dbname = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn.autocommit = True

    @staticmethod
    def parse_pattern(sql):
        command, _, arg = sql.partition(' ')
        verbose = '+' in command
        return (command.strip(), verbose, arg.strip())

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
            dbname = self.parse_pattern(sql)[2]
            self.conn = psycopg2.connect(database=dbname,
                    user=self.user, password=self.password, host=self.host,
                    port=self.port)
            self.dbname = dbname
            return [(None, None, 'You are now connected to database "%s" as '
                    'user "%s"' % (self.dbname, self.user))]

        with self.conn.cursor() as cur:
            try:
                results = pgspecial.execute(cur, *self.parse_pattern(sql))
                return results
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

    #def _meta_execute(self, sql, query_params=()):
        #with self.conn.cursor() as cur:
            #if query_params:
                #cur.execute(sql, query_params)
            #else:
                #cur.execute(sql)
            #return [x[0] for x in cur.fetchall()]
