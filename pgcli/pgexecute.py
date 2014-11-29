import psycopg2

class PGExecute(object):

    special_commands = {
            '\d': '''SELECT n.nspname as "Schema", c.relname as "Name", CASE c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized view' WHEN 'i' THEN 'index' WHEN 'S' THEN 'sequence' WHEN 's' THEN 'special' WHEN 'f' THEN 'foreign table' END as "Type", pg_catalog.pg_get_userbyid(c.relowner) as "Owner" FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r','v','m','S','f','') AND n.nspname <> 'pg_catalog' AND n.nspname <> 'information_schema' AND n.nspname !~ '^pg_toast' AND pg_catalog.pg_table_is_visible(c.oid) ORDER BY 1,2;''',
            '\dt': '''SELECT n.nspname as "Schema", c.relname as "Name", CASE c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized view' WHEN 'i' THEN 'index' WHEN 'S' THEN 'sequence' WHEN 's' THEN 'special' WHEN 'f' THEN 'foreign table' END as "Type", pg_catalog.pg_get_userbyid(c.relowner) as "Owner" FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r','') AND n.nspname <> 'pg_catalog' AND n.nspname <> 'information_schema' AND n.nspname !~ '^pg_toast' AND pg_catalog.pg_table_is_visible(c.oid) ORDER BY 1,2;'''
            }

    tables_query = '''SELECT c.relname as "Name" FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r','') AND n.nspname <> 'pg_catalog' AND n.nspname <> 'information_schema' AND n.nspname !~ '^pg_toast' AND pg_catalog.pg_table_is_visible(c.oid) ORDER BY 1;'''
    columns_query = '''SELECT column_name FROM information_schema.columns WHERE table_name =%s;'''

    def __init__(self, database, user, password, host, port):
        self.conn = psycopg2.connect(database=database, user=user,
                password=password, host=host, port=port)
        self.conn.autocommit = True

    def run(self, sql):
        sql = sql.strip()
        with self.conn.cursor() as cur:
            if sql in self.special_commands:
                cur.execute(self.special_commands[sql])
            else:
                cur.execute(sql)

            # cur.description will be None for operations that do not return
            # rows.
            if cur.description:
                headers = [x[0] for x in cur.description]
                return cur.fetchall(), headers, cur.statusmessage
            else:
                return None, None, cur.statusmessage

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
