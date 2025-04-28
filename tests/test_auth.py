import pytest
from unittest import mock
from pgcli import auth


@pytest.mark.parametrize("enabled,call_count", [(True, 1), (False, 0)])
def test_keyring_initialize(enabled, call_count):
    logger = mock.MagicMock()

    with mock.patch("importlib.import_module", return_value=True) as import_method:
        auth.keyring_initialize(enabled, logger=logger)
        assert import_method.call_count == call_count


def test_keyring_get_password_ok():
    with mock.patch("pgcli.auth.keyring", return_value=mock.MagicMock()):
        with mock.patch("pgcli.auth.keyring.get_password", return_value="abc123"):
            assert auth.keyring_get_password("test") == "abc123"


def test_keyring_get_password_exception():
    with mock.patch("pgcli.auth.keyring", return_value=mock.MagicMock()):
        with mock.patch("pgcli.auth.keyring.get_password", side_effect=Exception("Boom!")):
            assert auth.keyring_get_password("test") == ""


def test_keyring_set_password_ok():
    with mock.patch("pgcli.auth.keyring", return_value=mock.MagicMock()):
        with mock.patch("pgcli.auth.keyring.set_password"):
            auth.keyring_set_password("test", "abc123")


def test_keyring_set_password_exception():
    with mock.patch("pgcli.auth.keyring", return_value=mock.MagicMock()):
        with mock.patch("pgcli.auth.keyring.set_password", side_effect=Exception("Boom!")):
            auth.keyring_set_password("test", "abc123")
