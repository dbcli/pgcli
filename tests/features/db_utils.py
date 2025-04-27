from psycopg import connect


def create_db(hostname="localhost", username=None, password=None, dbname=None, port=None):
    """Create test database.

    :param hostname: string
    :param username: string
    :param password: string
    :param dbname: string
    :param port: int
    :return:

    """
    cn = create_cn(hostname, password, username, "postgres", port)

    cn.autocommit = True
    with cn.cursor() as cr:
        cr.execute(f"drop database if exists {dbname}")
        cr.execute(f"create database {dbname}")

    cn.close()

    cn = create_cn(hostname, password, username, dbname, port)
    return cn


def create_cn(hostname, password, username, dbname, port):
    """
    Open connection to database.
    :param hostname:
    :param password:
    :param username:
    :param dbname: string
    :return: psycopg2.connection
    """
    cn = connect(host=hostname, user=username, dbname=dbname, password=password, port=port)

    print(f"Created connection: {cn.info.get_parameters()}.")
    return cn


def pgbouncer_available(hostname="localhost", password=None, username="postgres"):
    cn = None
    try:
        cn = create_cn(hostname, password, username, "pgbouncer", 6432)
        return True
    except Exception:
        print("Pgbouncer is not available.")
    finally:
        if cn:
            cn.close()
    return False


def drop_db(hostname="localhost", username=None, password=None, dbname=None, port=None):
    """
    Drop database.
    :param hostname: string
    :param username: string
    :param password: string
    :param dbname: string
    """
    cn = create_cn(hostname, password, username, "postgres", port)

    # Needed for DB drop.
    cn.autocommit = True

    with cn.cursor() as cr:
        cr.execute(f"drop database if exists {dbname}")

    close_cn(cn)


def close_cn(cn=None):
    """
    Close connection.
    :param connection: psycopg2.connection
    """
    if cn:
        cn_params = cn.info.get_parameters()
        cn.close()
        print(f"Closed connection: {cn_params}.")
