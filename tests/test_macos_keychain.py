import ctypes
from unittest import mock

import pytest

from pgcli import macos_keychain


def test_set_password_preserves_access_list_when_updating():
    security = mock.MagicMock()
    core_foundation = mock.MagicMock()

    core_foundation.CFStringCreateWithCString.side_effect = [101, 102]
    core_foundation.CFDataCreate.return_value = 103
    core_foundation.CFDictionaryCreate.side_effect = [201, 202]
    security.SecItemUpdate.return_value = 0

    constants = (ctypes.c_void_p(value) for value in range(301, 310))
    with (
        mock.patch("pgcli.macos_keychain._load_framework", side_effect=[security, core_foundation]),
        mock.patch("pgcli.macos_keychain._constant", side_effect=constants),
    ):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    core_foundation.CFArrayCreate.assert_not_called()
    security.SecAccessCreate.assert_not_called()
    security.SecItemAdd.assert_not_called()


def test_set_password_uses_empty_access_list_when_creating():
    security = mock.MagicMock()
    core_foundation = mock.MagicMock()

    core_foundation.CFStringCreateWithCString.side_effect = [101, 102]
    core_foundation.CFDataCreate.return_value = 103
    core_foundation.CFArrayCreate.return_value = 104
    core_foundation.CFDictionaryCreate.side_effect = [201, 202, 203]
    security.SecAccessCreate.return_value = 0
    security.SecItemUpdate.return_value = macos_keychain._ITEM_NOT_FOUND
    security.SecItemAdd.return_value = 0

    constants = (ctypes.c_void_p(value) for value in range(301, 310))
    with (
        mock.patch("pgcli.macos_keychain._load_framework", side_effect=[security, core_foundation]),
        mock.patch("pgcli.macos_keychain._constant", side_effect=constants),
    ):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    core_foundation.CFArrayCreate.assert_called_once_with(None, None, 0, None)
    security.SecAccessCreate.assert_called_once()
    security.SecItemAdd.assert_called_once()


@pytest.mark.parametrize("keychain_path", [None, "/tmp/test.keychain"])
def test_set_password_scopes_legacy_operations_to_keychain(keychain_path):
    security = mock.MagicMock()
    core_foundation = mock.MagicMock()

    core_foundation.CFStringCreateWithCString.side_effect = [101, 102]
    core_foundation.CFDataCreate.return_value = 103
    core_foundation.CFArrayCreate.side_effect = [104, 105]
    core_foundation.CFDictionaryCreate.side_effect = [201, 202, 203]
    security.SecAccessCreate.return_value = 0
    security.SecKeychainCopyDefault.return_value = 0
    security.SecKeychainOpen.return_value = 0
    security.SecItemUpdate.return_value = macos_keychain._ITEM_NOT_FOUND
    security.SecItemAdd.return_value = 0

    constants = (ctypes.c_void_p(value) for value in range(301, 312))
    with (
        mock.patch("pgcli.macos_keychain._load_framework", side_effect=[security, core_foundation]),
        mock.patch("pgcli.macos_keychain._constant", side_effect=constants),
    ):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret", keychain_path)

    if keychain_path is None:
        security.SecKeychainCopyDefault.assert_called_once()
        security.SecKeychainOpen.assert_not_called()
    else:
        security.SecKeychainOpen.assert_called_once()
        security.SecKeychainCopyDefault.assert_not_called()
    assert core_foundation.CFArrayCreate.call_args_list[0].args[2:] == (
        1,
        core_foundation.kCFTypeArrayCallBacks,
    )
    assert core_foundation.CFArrayCreate.call_args_list[1] == mock.call(None, None, 0, None)
