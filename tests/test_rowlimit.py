from pgcli.main import PGCli
from mock import Mock
import pytest


# We need this fixtures beacause we need PGCli object to be created
# after test collection so it has config loaded from temp directory

@pytest.fixture(scope="module")
def default_pgcli_obj():
    return PGCli()


@pytest.fixture(scope="module")
def DEFAULT(default_pgcli_obj):
    return default_pgcli_obj.row_limit


@pytest.fixture(scope="module")
def LIMIT(DEFAULT):
    return DEFAULT + 1000


@pytest.fixture(scope="module")
def over_default(DEFAULT):
    over_default_cursor = Mock()
    over_default_cursor.configure_mock(
        rowcount=DEFAULT + 10
    )
    return over_default_cursor


@pytest.fixture(scope="module")
def over_limit(LIMIT):
    over_limit_cursor = Mock()
    over_limit_cursor.configure_mock(rowcount=LIMIT + 10)
    return over_limit_cursor


@pytest.fixture(scope="module")
def low_count():
    low_count_cursor = Mock()
    low_count_cursor.configure_mock(rowcount=1)
    return low_count_cursor


def test_default_row_limit(low_count, over_default):
    cli = PGCli()
    stmt = "SELECT * FROM students"
    result = cli._should_show_limit_prompt(stmt, low_count)
    assert result is False

    result = cli._should_show_limit_prompt(stmt, over_default)
    assert result is True


def test_set_row_limit(over_default, over_limit, LIMIT):
    cli = PGCli(row_limit=LIMIT)
    stmt = "SELECT * FROM students"
    result = cli._should_show_limit_prompt(stmt, over_default)
    assert result is False

    result = cli._should_show_limit_prompt(stmt, over_limit)
    assert result is True


def test_no_limit(over_limit):
    cli = PGCli(row_limit=0)
    stmt = "SELECT * FROM students"

    result = cli._should_show_limit_prompt(stmt, over_limit)
    assert result is False


def test_row_limit_on_non_select(over_default):
    cli = PGCli()
    stmt = "UPDATE students set name='Boby'"
    result = cli._should_show_limit_prompt(stmt, None)
    assert result is False

    cli = PGCli(row_limit=0)
    result = cli._should_show_limit_prompt(stmt, over_default)
    assert result is False
