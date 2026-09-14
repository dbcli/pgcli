import ctypes
from ctypes.util import find_library


_ITEM_NOT_FOUND = -25300
_UTF8 = 0x08000100
_UNSCOPED = object()


def _load_framework(name):
    path = find_library(name)
    if not path:
        raise RuntimeError(f"Unable to load the macOS {name} framework")
    return ctypes.CDLL(path)


def _constant(framework, name):
    return ctypes.c_void_p.in_dll(framework, name)


def _check_status(status):
    if status != 0:
        raise RuntimeError(f"macOS Keychain returned status {status}")


def set_password(service, account, password, keychain_path=_UNSCOPED):
    """Store a password without pre-authorizing the creating executable."""
    security = _load_framework("Security")
    core_foundation = _load_framework("CoreFoundation")

    cf_string_create = core_foundation.CFStringCreateWithCString
    cf_string_create.restype = ctypes.c_void_p
    cf_string_create.argtypes = (ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32)

    cf_data_create = core_foundation.CFDataCreate
    cf_data_create.restype = ctypes.c_void_p
    cf_data_create.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long)

    cf_array_create = core_foundation.CFArrayCreate
    cf_array_create.restype = ctypes.c_void_p
    cf_array_create.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long, ctypes.c_void_p)

    cf_dictionary_create = core_foundation.CFDictionaryCreate
    cf_dictionary_create.restype = ctypes.c_void_p
    cf_dictionary_create.argtypes = (
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_long,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )

    cf_release = core_foundation.CFRelease
    cf_release.argtypes = (ctypes.c_void_p,)

    sec_access_create = security.SecAccessCreate
    sec_access_create.restype = ctypes.c_int32
    sec_access_create.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))

    sec_item_add = security.SecItemAdd
    sec_item_add.restype = ctypes.c_int32
    sec_item_add.argtypes = (ctypes.c_void_p, ctypes.c_void_p)

    sec_item_update = security.SecItemUpdate
    sec_item_update.restype = ctypes.c_int32
    sec_item_update.argtypes = (ctypes.c_void_p, ctypes.c_void_p)

    retained = []

    def create_string(value):
        result = cf_string_create(None, value.encode("utf-8"), _UTF8)
        if not result:
            raise RuntimeError("Unable to allocate a Keychain string")
        retained.append(result)
        return result

    def create_dictionary(entries):
        keys = (ctypes.c_void_p * len(entries))(*(key for key, value in entries))
        values = (ctypes.c_void_p * len(entries))(*(value for key, value in entries))
        result = cf_dictionary_create(
            None,
            keys,
            values,
            len(entries),
            core_foundation.kCFTypeDictionaryKeyCallBacks,
            core_foundation.kCFTypeDictionaryValueCallBacks,
        )
        if not result:
            raise RuntimeError("Unable to allocate Keychain attributes")
        retained.append(result)
        return result

    try:
        service_value = create_string(service)
        account_value = create_string(account)
        password_bytes = password.encode("utf-8")
        password_buffer = ctypes.create_string_buffer(password_bytes)
        password_value = cf_data_create(None, password_buffer, len(password_bytes))
        if not password_value:
            raise RuntimeError("Unable to allocate Keychain password data")
        retained.append(password_value)

        identity_entries = [
            (_constant(security, "kSecClass"), _constant(security, "kSecClassGenericPassword")),
            (_constant(security, "kSecAttrService"), service_value),
            (_constant(security, "kSecAttrAccount"), account_value),
        ]
        search_entries = identity_entries.copy()
        add_entries = identity_entries.copy()

        if keychain_path is not _UNSCOPED:
            keychain = ctypes.c_void_p()
            if keychain_path is None:
                sec_keychain_copy_default = security.SecKeychainCopyDefault
                sec_keychain_copy_default.restype = ctypes.c_int32
                sec_keychain_copy_default.argtypes = (ctypes.POINTER(ctypes.c_void_p),)
                status = sec_keychain_copy_default(ctypes.byref(keychain))
            else:
                sec_keychain_open = security.SecKeychainOpen
                sec_keychain_open.restype = ctypes.c_int32
                sec_keychain_open.argtypes = (ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p))
                status = sec_keychain_open(keychain_path.encode(), ctypes.byref(keychain))
            _check_status(status)
            retained.append(keychain)

            keychain_values = (ctypes.c_void_p * 1)(keychain)
            search_list = cf_array_create(
                None,
                keychain_values,
                1,
                core_foundation.kCFTypeArrayCallBacks,
            )
            if not search_list:
                raise RuntimeError("Unable to allocate a Keychain search list")
            retained.append(search_list)

            search_entries.append((_constant(security, "kSecMatchSearchList"), search_list))
            add_entries.append((_constant(security, "kSecUseKeychain"), keychain))

        search = create_dictionary(search_entries)
        attributes = create_dictionary([(_constant(security, "kSecValueData"), password_value)])

        status = sec_item_update(search, attributes)
        if status == _ITEM_NOT_FOUND:
            trusted_apps = cf_array_create(None, None, 0, None)
            if not trusted_apps:
                raise RuntimeError("Unable to allocate Keychain access controls")
            retained.append(trusted_apps)

            access = ctypes.c_void_p()
            _check_status(sec_access_create(service_value, trusted_apps, ctypes.byref(access)))
            retained.append(access)

            item = create_dictionary(
                add_entries
                + [
                    (_constant(security, "kSecValueData"), password_value),
                    (_constant(security, "kSecAttrAccess"), access),
                ]
            )
            status = sec_item_add(item, None)
        _check_status(status)
    finally:
        for value in reversed(retained):
            cf_release(value)
