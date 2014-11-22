import psycopg2

class PGExecute(object):
    def __init__(self, database, user, password, host, port):
        self.conn = psycopg2.connect(database=database, user=user,
                password=password, host=host, port=port)

    def run(self, sql):
        with self.conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

