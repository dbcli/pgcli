# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import os
import pexpect
import db_utils as dbutils
import fixture_utils as fixutils


def before_all(context):
    """
    Set env parameters.
    """
    os.environ['LINES'] = "100"
    os.environ['COLUMNS'] = "100"
    os.environ['PAGER'] = 'cat'

    context.exit_sent = False

    # Store get params from config.
    context.conf = {
        'host': context.config.userdata.get('pg_test_host', 'localhost'),
        'user': context.config.userdata.get('pg_test_user', 'root'),
        'pass': context.config.userdata.get('pg_test_pass', None),
        'dbname': context.config.userdata.get('pg_test_db', None),
    }

    # Store old env vars.
    context.pgenv = {
        'PGDATABASE': os.environ.get('PGDATABASE', None),
        'PGUSER': os.environ.get('PGUSER', None),
        'PGHOST': os.environ.get('PGHOST', None),
        'PGPASS': os.environ.get('PGPASS', None),
    }

    # Set new env vars.
    os.environ['PGDATABASE'] = context.conf['dbname']
    os.environ['PGUSER'] = context.conf['user']
    os.environ['PGHOST'] = context.conf['host']
    if context.conf['pass']:
        os.environ['PGPASS'] = context.conf['pass']
    elif 'PGPASS' in os.environ:
        del os.environ['PGPASS']

    context.cn = dbutils.create_db(context.conf['host'], context.conf['user'],
                                   context.conf['pass'],
                                   context.conf['dbname'])

    context.fixture_data = fixutils.read_fixture_files()


def after_all(context):
    """
    Unset env parameters.
    """
    dbutils.close_cn(context.cn)
    dbutils.drop_db(context.conf['host'], context.conf['user'],
                    context.conf['pass'], context.conf['dbname'])

    # Restore env vars.
    for k, v in context.pgenv.items():
        if k in os.environ and v is None:
            del os.environ[k]
        elif v:
            os.environ[k] = v


def after_scenario(context, _):
    """
    Cleans up after each test complete.
    """

    if hasattr(context, 'cli') and not context.exit_sent:
        # Send Ctrl + D into cli
        context.cli.sendcontrol('d')
        context.cli.expect(pexpect.EOF)
