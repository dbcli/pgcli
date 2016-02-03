import os
import platform

import pytest
try:
    import setproctitle
except ImportError:
    setproctitle = None

from pgcli.main import obfuscate_process_password, format_output, PGCli
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
    results = format_output('Title', [('abc', 'def')], ['head1', 'head2'],
                            'test status', 'psql')
    expected = ['Title', '+---------+---------+\n| head1   | head2   |\n|---------+---------|\n| abc     | def     |\n+---------+---------+', 'test status']
    assert results == expected

def test_format_output_auto_expand():
    table_results = format_output('Title', [('abc', 'def')],
                                  ['head1', 'head2'], 'test status', 'psql',
                                  max_width=100)
    table = ['Title', '+---------+---------+\n| head1   | head2   |\n|---------+---------|\n| abc     | def     |\n+---------+---------+', 'test status']
    assert table_results == table

    expanded_results = format_output('Title', [('abc', 'def')],
                                     ['head1', 'head2'], 'test status', 'psql',
                                     max_width=1)
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
    statement = r"\i {}".format(sqlfile)
    run(executor, statement, pgspecial=cli.pgspecial)


def test_missing_rc_dir(tmpdir):
    rcfile = str(tmpdir.join("subdir").join("rcfile"))

    cli = PGCli(
        pgclirc_file=rcfile,
    )
    assert os.path.exists(rcfile)
