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
    with mock.patch("pgcli.auth.platform.system", return_value="Linux"):
        with mock.patch("pgcli.auth.keyring", return_value=mock.MagicMock()):
            with mock.patch("pgcli.auth.keyring.set_password"):
                auth.keyring_set_password("test", "abc123")


@pytest.mark.parametrize("chained", [False, True])
def test_keyring_set_password_macos_has_no_trusted_apps(chained):
    backend_class = type("Keyring", (), {"__module__": "keyring.backends.macOS"})
    backend = backend_class()
    if chained:
        chainer_class = type("ChainerBackend", (), {"__module__": "keyring.backends.chainer"})
        configured_backend = chainer_class()
        configured_backend.backends = [backend]
    else:
        configured_backend = backend
    keyring = mock.Mock()
    keyring.get_keyring.return_value = configured_backend

    with (
        mock.patch("pgcli.auth.platform.system", return_value="Darwin"),
        mock.patch("pgcli.auth.keyring", keyring),
        mock.patch("pgcli.auth._macos_keyring_uses_keychain_path", return_value=False),
        mock.patch("pgcli.macos_keychain.set_password") as set_password,
    ):
        auth.keyring_set_password("test", "abc123")

    set_password.assert_called_once_with("pgcli", "test", "abc123")
    keyring.set_password.assert_not_called()


def test_keyring_set_password_macos_custom_backend():
    native_backend_class = type("Keyring", (), {"__module__": "keyring.backends.macOS"})
    backend_class = type("CompositeKeyring", (), {"__module__": "custom.keyring"})
    backend = backend_class()
    backend.backends = [native_backend_class()]
    keyring = mock.Mock()
    keyring.get_keyring.return_value = backend

    with (
        mock.patch("pgcli.auth.platform.system", return_value="Darwin"),
        mock.patch("pgcli.auth.keyring", keyring),
        mock.patch("pgcli.macos_keychain.set_password") as set_password,
    ):
        auth.keyring_set_password("test", "abc123")

    keyring.set_password.assert_called_once_with("pgcli", "test", "abc123")
    set_password.assert_not_called()


def test_keyring_set_password_macos_after_read_only_chained_backend():
    read_only_backend = mock.Mock()
    read_only_backend.set_password.side_effect = NotImplementedError
    native_backend_class = type("Keyring", (), {"__module__": "keyring.backends.macOS"})
    native_backend = native_backend_class()
    chainer_class = type("ChainerBackend", (), {"__module__": "keyring.backends.chainer"})
    configured_backend = chainer_class()
    configured_backend.backends = [read_only_backend, native_backend]
    keyring = mock.Mock()
    keyring.get_keyring.return_value = configured_backend

    with (
        mock.patch("pgcli.auth.platform.system", return_value="Darwin"),
        mock.patch("pgcli.auth.keyring", keyring),
        mock.patch("pgcli.auth._macos_keyring_uses_keychain_path", return_value=False),
        mock.patch("pgcli.macos_keychain.set_password") as set_password,
    ):
        auth.keyring_set_password("test", "abc123")

    read_only_backend.set_password.assert_called_once_with("pgcli", "test", "abc123")
    set_password.assert_called_once_with("pgcli", "test", "abc123")


@pytest.mark.parametrize("keychain_path", [None, "/tmp/test.keychain"])
def test_keyring_set_password_legacy_macos_preserves_keychain(keychain_path):
    backend_class = type("Keyring", (), {"__module__": "keyring.backends.OS_X"})
    backend = backend_class()
    backend.keychain = keychain_path
    keyring = mock.Mock()
    keyring.get_keyring.return_value = backend

    with (
        mock.patch("pgcli.auth.platform.system", return_value="Darwin"),
        mock.patch("pgcli.auth.keyring", keyring),
        mock.patch("pgcli.macos_keychain.set_password") as set_password,
    ):
        auth.keyring_set_password("test", "abc123")

    set_password.assert_called_once_with("pgcli", "test", "abc123", keychain_path)


def test_keyring_set_password_transitional_macos_preserves_keychain():
    backend_class = type("Keyring", (), {"__module__": "keyring.backends.macOS"})
    backend = backend_class()
    backend.keychain = "/tmp/test.keychain"
    keyring = mock.Mock()
    keyring.get_keyring.return_value = backend

    with (
        mock.patch("pgcli.auth.platform.system", return_value="Darwin"),
        mock.patch("pgcli.auth.keyring", keyring),
        mock.patch("pgcli.auth._macos_keyring_uses_keychain_path", return_value=True),
        mock.patch("pgcli.macos_keychain.set_password") as set_password,
    ):
        auth.keyring_set_password("test", "abc123")

    set_password.assert_called_once_with("pgcli", "test", "abc123", "/tmp/test.keychain")


@pytest.mark.parametrize("has_scoped_api", [False, True])
def test_macos_keyring_path_capability_detection(has_scoped_api):
    backend_class = type("Keyring", (), {"__module__": "keyring.backends.macOS"})
    backend_api = object()
    if has_scoped_api:
        backend_api = mock.Mock(SecKeychainCopyDefault=mock.Mock())

    with mock.patch("importlib.import_module", return_value=mock.Mock(api=backend_api)):
        assert auth._macos_keyring_uses_keychain_path(backend_class()) is has_scoped_api


def test_keyring_set_password_exception():
    with mock.patch("pgcli.auth.platform.system", return_value="Linux"):
        with mock.patch("pgcli.auth.keyring", return_value=mock.MagicMock()):
            with mock.patch("pgcli.auth.keyring.set_password", side_effect=Exception("Boom!")):
                auth.keyring_set_password("test", "abc123")
