from pgcli.main import PGCli
from mock import Mock

DEFAULT = PGCli().row_limit
LIMIT = DEFAULT + 1000


over_default = Mock()
over_default.configure_mock(rowcount=DEFAULT + 10)

over_limit = Mock()
over_limit.configure_mock(rowcount=LIMIT + 10)

low_count = Mock()
low_count.configure_mock(rowcount=1)


def test_default_row_limit():
    cli = PGCli()
    stmt = "SELECT * FROM students"
    result = cli._should_show_limit_prompt(stmt, low_count)
    assert result is False

    result = cli._should_show_limit_prompt(stmt, over_default)
    assert result is True


def test_set_row_limit():
    cli = PGCli(row_limit=LIMIT)
    stmt = "SELECT * FROM students"
    result = cli._should_show_limit_prompt(stmt, over_default)
    assert result is False

    result = cli._should_show_limit_prompt(stmt, over_limit)
    assert result is True


def test_no_limit():
    cli = PGCli(row_limit=0)
    stmt = "SELECT * FROM students"

    result = cli._should_show_limit_prompt(stmt, over_limit)
    assert result is False


def test_row_limit_on_non_select():
    cli = PGCli()
    stmt = "UPDATE students set name='Boby'"
    result = cli._should_show_limit_prompt(stmt, None)
    assert result is False

    cli = PGCli(row_limit=0)
    result = cli._should_show_limit_prompt(stmt, over_default)
    assert result is False
