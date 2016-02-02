import pytest
import platform
try:
    import setproctitle
except ImportError:
    setproctitle = None

from pgcli.main import obfuscate_process_password, format_output, LESS_DEFAULTS, PGCli, output_fits_screen
from collections import namedtuple

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

def test_display_output():
    pass

def test_output_fits_screen():
    # Mock ScreenSize for tests
    ScreenSize = namedtuple('ScreenSize', ['columns', 'rows'])
    prepared_output = ['Title', '+---------+---------+\n| head1   | head2   |\n|---------+---------|\n| abc     | def     |\n+---------+---------+', 'test status']
    screen_size = ScreenSize(columns=22, rows=5)
    assert output_fits_screen(prepared_output, screen_size) is True
    screen_size = ScreenSize(columns=20, rows=5)
    assert output_fits_screen(prepared_output, screen_size) is False
    screen_size = ScreenSize(columns=22, rows=4)
    assert output_fits_screen(prepared_output, screen_size) is False

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

def test_less_opts():
    import os
    original_less_opts = os.environ.get('LESS', '')
    cli = PGCli.__new__(PGCli)
    less_options_adjusted = cli.adjust_less_opts()
    assert os.environ['LESS'] == LESS_DEFAULTS
    assert less_options_adjusted is True
    os.environ['LESS'] = '-lmnropst'
    less_options_adjusted = cli.adjust_less_opts()
    assert os.environ['LESS'] == '-lmnropst'
    assert less_options_adjusted is False
    os.environ['LESS'] = original_less_opts

