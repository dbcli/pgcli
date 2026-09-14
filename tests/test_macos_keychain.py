import ctypes
from types import SimpleNamespace
from unittest import mock

import pytest

from pgcli import macos_keychain


def keyring_api(update_status):
    found = mock.MagicMock()
    security = mock.MagicMock()
    error = SimpleNamespace(item_not_found=-25300)
    api = SimpleNamespace(
        _found=found,
        _sec=security,
        OS_status=ctypes.c_int32,
        error=error,
        Error=mock.MagicMock(),
        create_cf=mock.Mock(side_effect=[101, 102, 103]),
        create_query=mock.Mock(side_effect=[201, 202, 203]),
        k_=mock.Mock(return_value=ctypes.c_void_p(301)),
        SecItemAdd=mock.Mock(return_value=0),
    )
    found.CFArrayCreate.return_value = 204

    def create_access(descriptor, trusted_apps, result):
        ctypes.cast(result, ctypes.POINTER(ctypes.c_void_p))[0] = ctypes.c_void_p(205)
        return 0

    security.SecAccessCreate.side_effect = create_access
    security.SecItemUpdate.return_value = update_status
    return api


def test_set_password_preserves_access_list_when_updating():
    api = keyring_api(update_status=0)

    with mock.patch("pgcli.macos_keychain._get_api", return_value=api):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    api._found.CFArrayCreate.assert_not_called()
    api._sec.SecAccessCreate.assert_not_called()
    api.SecItemAdd.assert_not_called()
    api.Error.raise_for_status.assert_called_once_with(0)
    assert [
        call.args[0].value if isinstance(call.args[0], ctypes.c_void_p) else call.args[0] for call in api._found.CFRelease.call_args_list
    ] == [
        202,
        201,
        103,
        102,
        101,
    ]


@pytest.mark.parametrize("create_string", ["create_cfstr", "create_cf"])
def test_set_password_uses_empty_access_list_when_creating(create_string):
    api_item_not_found = -25300
    api = keyring_api(update_status=api_item_not_found)
    if create_string == "create_cfstr":
        api.create_cfstr = mock.Mock(side_effect=[101, 102, 103])

    with mock.patch("pgcli.macos_keychain._get_api", return_value=api):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    assert api.error.item_not_found == api_item_not_found
    api._found.CFArrayCreate.assert_called_once_with(None, None, 0, None)
    api._sec.SecAccessCreate.assert_called_once()
    api.SecItemAdd.assert_called_once_with(203, None)
    assert getattr(api, create_string).call_args_list == [
        mock.call("pgcli"),
        mock.call("user@host@5432"),
        mock.call("secret"),
    ]
    assert api.create_query.call_args_list == [
        mock.call(
            kSecClass=api.k_.return_value,
            kSecAttrService=mock.ANY,
            kSecAttrAccount=mock.ANY,
        ),
        mock.call(kSecValueData=mock.ANY),
        mock.call(
            kSecClass=api.k_.return_value,
            kSecAttrService=mock.ANY,
            kSecAttrAccount=mock.ANY,
            kSecValueData=mock.ANY,
            kSecAttrAccess=mock.ANY,
        ),
    ]
    search = api.create_query.call_args_list[0].kwargs
    attributes = api.create_query.call_args_list[1].kwargs
    item = api.create_query.call_args_list[2].kwargs
    assert search["kSecAttrService"].value == item["kSecAttrService"].value == 101
    assert search["kSecAttrAccount"].value == item["kSecAttrAccount"].value == 102
    assert attributes["kSecValueData"].value == item["kSecValueData"].value == 103
    assert api.create_query.call_args_list[2].kwargs["kSecAttrAccess"].value == 205


def test_set_password_rejects_missing_access_list():
    api = keyring_api(update_status=-25300)
    api._found.CFArrayCreate.return_value = None

    with (
        mock.patch("pgcli.macos_keychain._get_api", return_value=api),
        pytest.raises(RuntimeError, match="Unable to allocate Keychain access controls"),
    ):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    api._sec.SecAccessCreate.assert_not_called()
    api.SecItemAdd.assert_not_called()
