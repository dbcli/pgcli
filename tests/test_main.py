import pytest
from pgcli.main import need_completion_refresh


@pytest.mark.parametrize('sql', [
    'DROP TABLE foo',
    'SELECT * FROM foo; DROP TABLE foo',
])
def test_need_completion_refresh(sql):
    assert need_completion_refresh(sql)