import ctypes


def _get_api():
    from keyring.backends.macOS import api

    return api


def _create_string(api, value):
    create_string = getattr(api, "create_cfstr", None) or api.create_cf
    result = create_string(value)
    return result if isinstance(result, ctypes.c_void_p) else ctypes.c_void_p(result)


def set_password(service, account, password):
    """Store a password without pre-authorizing the creating executable."""
    api = _get_api()

    cf_array_create = api._found.CFArrayCreate
    cf_array_create.restype = ctypes.c_void_p
    cf_array_create.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long, ctypes.c_void_p)

    cf_release = api._found.CFRelease
    cf_release.restype = None
    cf_release.argtypes = (ctypes.c_void_p,)

    sec_access_create = api._sec.SecAccessCreate
    sec_access_create.restype = api.OS_status
    sec_access_create.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))

    sec_item_update = api._sec.SecItemUpdate
    sec_item_update.restype = api.OS_status
    sec_item_update.argtypes = (ctypes.c_void_p, ctypes.c_void_p)

    retained = []

    def retain(value, error):
        if not value:
            raise RuntimeError(error)
        retained.append(value)
        return value

    try:
        service_value = retain(_create_string(api, service), "Unable to allocate Keychain service")
        account_value = retain(_create_string(api, account), "Unable to allocate Keychain account")
        password_value = retain(_create_string(api, password), "Unable to allocate Keychain password")

        search = retain(
            api.create_query(
                kSecClass=api.k_("kSecClassGenericPassword"),
                kSecAttrService=service_value,
                kSecAttrAccount=account_value,
            ),
            "Unable to allocate Keychain search",
        )
        attributes = retain(
            api.create_query(kSecValueData=password_value),
            "Unable to allocate Keychain attributes",
        )

        status = sec_item_update(search, attributes)
        if status == api.error.item_not_found:
            trusted_apps = retain(
                cf_array_create(None, None, 0, None),
                "Unable to allocate Keychain access controls",
            )

            access = ctypes.c_void_p()
            api.Error.raise_for_status(sec_access_create(service_value, trusted_apps, ctypes.byref(access)))
            retain(access, "Unable to allocate Keychain access")

            item = retain(
                api.create_query(
                    kSecClass=api.k_("kSecClassGenericPassword"),
                    kSecAttrService=service_value,
                    kSecAttrAccount=account_value,
                    kSecValueData=password_value,
                    kSecAttrAccess=access,
                ),
                "Unable to allocate Keychain item",
            )
            status = api.SecItemAdd(item, None)
        api.Error.raise_for_status(status)
    finally:
        for value in reversed(retained):
            cf_release(value)
