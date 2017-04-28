# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import os
import sys
import db_utils as dbutils
import fixture_utils as fixutils
import pexpect


def before_all(context):
    """
    Set env parameters.
    """
    os.environ['LINES'] = "100"
    os.environ['COLUMNS'] = "100"
    os.environ['PAGER'] = 'cat'
    os.environ['EDITOR'] = 'ex'
    os.environ["COVERAGE_PROCESS_START"] = os.getcwd() + "/../.coveragerc"

    context.exit_sent = False

    vi = '_'.join([str(x) for x in sys.version_info[:3]])
    db_name = context.config.userdata.get('pg_test_db', None)
    db_name_full = '{0}_{1}'.format(db_name, vi)

    # Store get params from config.
    context.conf = {
        'host': context.config.userdata.get('pg_test_host', 'localhost'),
        'user': context.config.userdata.get('pg_test_user', 'postgres'),
        'pass': context.config.userdata.get('pg_test_pass', None),
        'dbname': db_name_full,
        'dbname_tmp': db_name_full + '_tmp',
        'vi': vi,
        'cli_command': context.config.userdata.get('pg_cli_command', None) or
                       sys.executable +
        ' -c "import coverage; coverage.process_startup(); import pgcli.main; pgcli.main.cli()"',
        'pager_boundary': '---boundary---',
    }
    os.environ['PAGER'] = "{0} {1} {2}".format(
        sys.executable, "tests/features/wrappager.py",
        context.conf['pager_boundary']
    )

    # Store old env vars.
    context.pgenv = {
        'PGDATABASE': os.environ.get('PGDATABASE', None),
        'PGUSER': os.environ.get('PGUSER', None),
        'PGHOST': os.environ.get('PGHOST', None),
        'PGPASSWORD': os.environ.get('PGPASSWORD', None),
    }

    # Set new env vars.
    os.environ['PGDATABASE'] = context.conf['dbname']
    os.environ['PGUSER'] = context.conf['user']
    os.environ['PGHOST'] = context.conf['host']

    if context.conf['pass']:
        os.environ['PGPASSWORD'] = context.conf['pass']
    else:
        if 'PGPASSWORD' in os.environ:
            del os.environ['PGPASSWORD']
        if 'PGHOST' in os.environ:
            del os.environ['PGHOST']

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


def before_step(context, _):
    context.atprompt = False


def after_scenario(context, _):
    """Cleans up after each test complete."""

    if hasattr(context, 'cli') and not context.exit_sent:
        # Quit nicely.
        if not context.atprompt:
            dbname = context.currentdb
            context.cli.expect_exact(
                '{0}> '.format(dbname),
                timeout=5
            )
        context.cli.sendcontrol('d')
        context.cli.expect_exact(pexpect.EOF, timeout=5)

# TODO: uncomment to debug a failure
# def after_step(context, step):
#     if step.status == "failed":
#         import ipdb; ipdb.set_trace()
