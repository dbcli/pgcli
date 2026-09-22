import ctypes
from types import SimpleNamespace
from unittest import mock

import pytest

from pgcli import macos_keychain


class KeychainError(Exception):
    pass


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

    def raise_for_status(status):
        if status:
            raise KeychainError(status)

    api.Error.raise_for_status.side_effect = raise_for_status
    return api


def released_references(api):
    return [
        call.args[0].value if isinstance(call.args[0], ctypes.c_void_p) else call.args[0] for call in api._found.CFRelease.call_args_list
    ]


def test_set_password_preserves_access_list_when_updating():
    api = keyring_api(update_status=0)

    with mock.patch("pgcli.macos_keychain._get_api", return_value=api):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    api._found.CFArrayCreate.assert_not_called()
    api._sec.SecAccessCreate.assert_not_called()
    api.SecItemAdd.assert_not_called()
    api.Error.raise_for_status.assert_called_once_with(0)
    assert released_references(api) == [202, 201, 103, 102, 101]


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
    assert released_references(api) == [203, 205, 204, 202, 201, 103, 102, 101]


@pytest.mark.parametrize("create_string", ["create_cfstr", "create_cf"])
@pytest.mark.parametrize(
    "allocation, expected_releases",
    [
        ("service", []),
        ("account", [101]),
        ("password", [102, 101]),
        ("search", [103, 102, 101]),
        ("attributes", [201, 103, 102, 101]),
        ("access controls", [202, 201, 103, 102, 101]),
        ("access", [204, 202, 201, 103, 102, 101]),
        ("item", [205, 204, 202, 201, 103, 102, 101]),
    ],
)
def test_set_password_releases_references_after_allocation_failure(create_string, allocation, expected_releases):
    api = keyring_api(update_status=-25300)
    strings = [101, 102, 103]
    queries = [201, 202, 203]
    if allocation in ("service", "account", "password"):
        strings[("service", "account", "password").index(allocation)] = None
    elif allocation in ("search", "attributes", "item"):
        queries[("search", "attributes", "item").index(allocation)] = None
    elif allocation == "access controls":
        api._found.CFArrayCreate.return_value = None
    else:
        # A successful status with a null output must also be rejected.
        api._sec.SecAccessCreate.side_effect = None
        api._sec.SecAccessCreate.return_value = 0
    del api.create_cf
    setattr(api, create_string, mock.Mock(side_effect=strings))
    api.create_query.side_effect = queries

    with (
        mock.patch("pgcli.macos_keychain._get_api", return_value=api),
        pytest.raises(RuntimeError, match=f"Unable to allocate Keychain {allocation}$"),
    ):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    assert released_references(api) == expected_releases
    api.SecItemAdd.assert_not_called()
    if allocation not in ("access", "item"):
        api._sec.SecAccessCreate.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [
        pytest.param(-128, id="cancelled"),
        pytest.param(-25293, id="authentication-failed"),
        pytest.param(-25308, id="interaction-not-allowed"),
        pytest.param(-50, id="invalid-parameter"),
        pytest.param(-25299, id="duplicate-item"),
    ],
)
@pytest.mark.parametrize("operation", ["SecItemUpdate", "SecAccessCreate", "SecItemAdd"])
def test_set_password_releases_references_after_security_error(operation, status):
    api = keyring_api(update_status=-25300)
    function = api.SecItemAdd if operation == "SecItemAdd" else getattr(api._sec, operation)
    function.side_effect = None
    function.return_value = status

    with (
        mock.patch("pgcli.macos_keychain._get_api", return_value=api),
        pytest.raises(KeychainError) as exc,
    ):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    assert exc.value.args == (status,)
    expected_releases = [202, 201, 103, 102, 101]
    if operation == "SecAccessCreate":
        expected_releases = [204] + expected_releases
    elif operation == "SecItemAdd":
        expected_releases = [203, 205, 204] + expected_releases
    assert released_references(api) == expected_releases
    if operation != "SecItemAdd":
        api.SecItemAdd.assert_not_called()
    if operation == "SecItemUpdate":
        api._sec.SecAccessCreate.assert_not_called()


@pytest.mark.parametrize(
    "operation, expected_releases",
    [
        ("SecItemUpdate", [202, 201, 103, 102, 101]),
        ("SecAccessCreate", [204, 202, 201, 103, 102, 101]),
        ("SecItemAdd", [203, 205, 204, 202, 201, 103, 102, 101]),
    ],
)
def test_set_password_releases_references_after_exception(operation, expected_releases):
    api = keyring_api(update_status=-25300)
    function = api.SecItemAdd if operation == "SecItemAdd" else getattr(api._sec, operation)
    error = OSError("Foreign function call failed")
    function.side_effect = error

    with (
        mock.patch("pgcli.macos_keychain._get_api", return_value=api),
        pytest.raises(OSError) as exc,
    ):
        macos_keychain.set_password("pgcli", "user@host@5432", "secret")

    assert exc.value is error
    assert released_references(api) == expected_releases
