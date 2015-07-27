# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from psycopg2 import connect
from psycopg2.extensions import AsIs


def create_db(hostname='localhost', username=None, password=None,
              dbname=None):
    """
    Create test database.
    :param hostname: string
    :param username: string
    :param password: string
    :param dbname: string
    :return:
    """
    cn = create_cn(hostname, password, username, 'postgres')

    # ISOLATION_LEVEL_AUTOCOMMIT = 0
    # Needed for DB creation.
    cn.set_isolation_level(0)

    with cn.cursor() as cr:
        cr.execute('drop database if exists %s', (AsIs(dbname),))
        cr.execute('create database %s', (AsIs(dbname),))

    cn.close()

    cn = create_cn(hostname, password, username, dbname)
    return cn


def create_cn(hostname, password, username, dbname):
    """
    Open connection to database.
    :param hostname:
    :param password:
    :param username:
    :param dbname: string
    :return: psycopg2.connection
    """
    if password:
        cn = connect(host=hostname, user=username, database=dbname,
                     password=password)
    else:
        cn = connect(user=username, database=dbname)

    print('Created connection: {0}.'.format(cn.dsn))
    return cn


def drop_db(hostname='localhost', username=None, password=None,
            dbname=None):
    """
    Drop database.
    :param hostname: string
    :param username: string
    :param password: string
    :param dbname: string
    """
    cn = create_cn(hostname, password, username, 'postgres')

    # ISOLATION_LEVEL_AUTOCOMMIT = 0
    # Needed for DB drop.
    cn.set_isolation_level(0)

    with cn.cursor() as cr:
        cr.execute('drop database if exists %s', (AsIs(dbname),))

    close_cn(cn)


def close_cn(cn=None):
    """
    Close connection.
    :param connection: psycopg2.connection
    """
    if cn:
        cn.close()
        print('Closed connection: {0}.'.format(cn.dsn))
