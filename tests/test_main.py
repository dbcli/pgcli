import os
import platform
import mock

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
    expected = ['Title', '+---------+---------+\n| head1   | head2   |\n|---------+---------|\n| abc     | def     |\n+---------+---------+', 'test status']
    assert results == expected

def test_format_output_auto_expand():
    settings = OutputSettings(table_format='psql', dcmlfmt='d', floatfmt='g', max_width=100)
    table_results = format_output('Title', [('abc', 'def')],
                                  ['head1', 'head2'], 'test status', settings)
    table = ['Title', '+---------+---------+\n| head1   | head2   |\n|---------+---------|\n| abc     | def     |\n+---------+---------+', 'test status']
    assert table_results == table
    expanded_results = format_output('Title', [('abc', 'def')],
                                     ['head1', 'head2'], 'test status', settings._replace(max_width=1))
    expanded = ['Title', u'-[ RECORD 0 ]-------------------------\nhead1 | abc\nhead2 | def\n', 'test status']
    assert expanded_results == expanded


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


def test_search_socketdir():
    cli = PGCli()
    with mock.patch('pgcli.main.os.path.isdir', autospec=True) as isdir:
        isdir.side_effect = iter([
            False, False, True, AssertionError("not reached"),
        ])

        socketdir = cli.guess_socketdir()

        assert isdir.called is True
        assert '/usr/local/var/postgres' == socketdir
