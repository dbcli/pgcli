# coding=utf-8
from __future__ import unicode_literals
import os
import platform
import mock
from decimal import Decimal

import pytest
try:
    import setproctitle
except ImportError:
    setproctitle = None

from pgcli.main import (
    obfuscate_process_password, format_output, PGCli, OutputSettings
)
from utils import dbtest, run


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason='Not applicable in windows')
@pytest.mark.skipif(not setproctitle,
                    reason='setproctitle not available')
def test_obfuscate_process_password():
    original_title = setproctitle.getproctitle()

    setproctitle.setproctitle("pgcli user=root password=secret host=localhost")
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    expected = "pgcli user=root password=xxxx host=localhost"
    assert title == expected

    setproctitle.setproctitle("pgcli user=root password=top secret host=localhost")
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    expected = "pgcli user=root password=xxxx host=localhost"
    assert title == expected

    setproctitle.setproctitle("pgcli user=root password=top secret")
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    expected = "pgcli user=root password=xxxx"
    assert title == expected

    setproctitle.setproctitle("pgcli postgres://root:secret@localhost/db")
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    expected = "pgcli postgres://root:xxxx@localhost/db"
    assert title == expected

    setproctitle.setproctitle(original_title)


def test_format_output():
    settings = OutputSettings(table_format='psql', dcmlfmt='d', floatfmt='g')
    results = format_output('Title', [('abc', 'def')], ['head1', 'head2'],
                            'test status', settings)
    expected = [
        'Title',
        '+---------+---------+',
        '| head1   | head2   |',
        '|---------+---------|',
        '| abc     | def     |',
        '+---------+---------+',
        'test status'
    ]
    assert list(results) == expected


@dbtest
def test_format_array_output(executor):
    statement = u"""
    SELECT
        array[1, 2, 3]::bigint[] as bigint_array,
        '{{1,2},{3,4}}'::numeric[] as nested_numeric_array,
        '{å,魚,текст}'::text[] as 配列
    UNION ALL
    SELECT '{}', NULL, array[NULL]
    """
    results = run(executor, statement)
    expected = [
        '+----------------+------------------------+--------------+',
        '| bigint_array   | nested_numeric_array   | 配列         |',
        '|----------------+------------------------+--------------|',
        '| {1,2,3}        | {{1,2},{3,4}}          | {å,魚,текст} |',
        '| {}             | <null>                 | {<null>}     |',
        '+----------------+------------------------+--------------+',
        'SELECT 2'
    ]
    assert list(results) == expected


@dbtest
def test_format_array_output_expanded(executor):
    statement = u"""
    SELECT
        array[1, 2, 3]::bigint[] as bigint_array,
        '{{1,2},{3,4}}'::numeric[] as nested_numeric_array,
        '{å,魚,текст}'::text[] as 配列
    UNION ALL
    SELECT '{}', NULL, array[NULL]
    """
    results = run(executor, statement, expanded=True)
    expected = [
        '-[ RECORD 1 ]-------------------------',
        'bigint_array         | {1,2,3}',
        'nested_numeric_array | {{1,2},{3,4}}',
        '配列                   | {å,魚,текст}',
        '-[ RECORD 2 ]-------------------------',
        'bigint_array         | {}',
        'nested_numeric_array | <null>',
        '配列                   | {<null>}',
        'SELECT 2'
    ]
    assert '\n'.join(results) == '\n'.join(expected)


def test_format_output_auto_expand():
    settings = OutputSettings(
        table_format='psql', dcmlfmt='d', floatfmt='g', max_width=100)
    table_results = format_output('Title', [('abc', 'def')],
                                  ['head1', 'head2'], 'test status', settings)
    table = [
        'Title',
        '+---------+---------+',
        '| head1   | head2   |',
        '|---------+---------|',
        '| abc     | def     |',
        '+---------+---------+',
        'test status'
    ]
    assert list(table_results) == table
    expanded_results = format_output(
        'Title',
        [('abc', 'def')],
        ['head1', 'head2'],
        'test status',
        settings._replace(max_width=1)
    )
    expanded = [
        'Title',
        '-[ RECORD 1 ]-------------------------',
        'head1 | abc',
        'head2 | def',
        'test status'
    ]
    assert '\n'.join(expanded_results) == '\n'.join(expanded)


@dbtest
def test_i_works(tmpdir, executor):
    sqlfile = tmpdir.join("test.sql")
    sqlfile.write("SELECT NOW()")
    rcfile = str(tmpdir.join("rcfile"))
    cli = PGCli(
        pgexecute=executor,
        pgclirc_file=rcfile,
    )
    statement = r"\i {0}".format(sqlfile)
    run(executor, statement, pgspecial=cli.pgspecial)


def test_missing_rc_dir(tmpdir):
    rcfile = str(tmpdir.join("subdir").join("rcfile"))

    PGCli(pgclirc_file=rcfile)
    assert os.path.exists(rcfile)


def test_quoted_db_uri(tmpdir):
    with mock.patch.object(PGCli, 'connect') as mock_connect:
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        cli.connect_uri('postgres://bar%5E:%5Dfoo@baz.com/testdb%5B')
    mock_connect.assert_called_with(database='testdb[',
                                    port=None,
                                    host='baz.com',
                                    user='bar^',
                                    passwd=']foo')


def test_ssl_db_uri(tmpdir):
    with mock.patch.object(PGCli, 'connect') as mock_connect:
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        cli.connect_uri(
            'postgres://bar%5E:%5Dfoo@baz.com/testdb%5B?'
            'sslmode=verify-full&sslcert=m%79.pem&sslkey=my-key.pem&sslrootcert=c%61.pem')
    mock_connect.assert_called_with(database='testdb[',
                                    host='baz.com',
                                    port=None,
                                    user='bar^',
                                    passwd=']foo',
                                    sslmode='verify-full',
                                    sslcert='my.pem',
                                    sslkey='my-key.pem',
                                    sslrootcert='ca.pem')


def test_port_db_uri(tmpdir):
    with mock.patch.object(PGCli, 'connect') as mock_connect:
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        cli.connect_uri('postgres://bar:foo@baz.com:2543/testdb')
    mock_connect.assert_called_with(database='testdb',
                                    host='baz.com',
                                    user='bar',
                                    passwd='foo',
                                    port='2543')
