import click
import platform
from textwrap import dedent


keyring = None  # keyring will be loaded later


keyring_error_message = dedent(
    """\
    {}
    {}
    To remove this message do one of the following:
    - prepare keyring as described at: https://keyring.readthedocs.io/en/stable/
    - uninstall keyring: pip uninstall keyring
    - disable keyring in our configuration: add keyring = False to [main]"""
)


def keyring_initialize(keyring_enabled, *, logger):
    """Initialize keyring only if explicitly enabled"""
    global keyring

    if keyring_enabled:
        # Try best to load keyring (issue #1041).
        import importlib

        try:
            keyring = importlib.import_module("keyring")
        except ModuleNotFoundError as e:  # ImportError for Python 2, ModuleNotFoundError for Python 3
            logger.warning("import keyring failed: %r.", e)


def keyring_get_password(key):
    """Attempt to get password from keyring"""
    # Find password from store
    passwd = ""
    try:
        passwd = keyring.get_password("pgcli", key) or ""
    except Exception as e:
        click.secho(
            keyring_error_message.format("Load your password from keyring returned:", str(e)),
            err=True,
            fg="red",
        )
    return passwd


def _is_macos_keyring_backend(backend):
    return backend.__class__.__module__ in {
        "keyring.backends.macOS",
        "keyring.backends.OS_X",
    }


def _macos_keyring_uses_keychain_path(backend):
    if backend.__class__.__module__ == "keyring.backends.OS_X":
        return True

    import importlib

    backend_module = importlib.import_module(backend.__class__.__module__)
    return hasattr(backend_module.api, "SecKeychainCopyDefault")


def _set_password_with_backend(backend, key, passwd):
    if _is_macos_keyring_backend(backend):
        from pgcli import macos_keychain

        if _macos_keyring_uses_keychain_path(backend):
            macos_keychain.set_password("pgcli", key, passwd, backend.keychain)
        else:
            macos_keychain.set_password("pgcli", key, passwd)
    else:
        backend.set_password("pgcli", key, passwd)


def keyring_set_password(key, passwd):
    try:
        configured_backend = keyring.get_keyring() if platform.system() == "Darwin" else None
        if configured_backend is not None and configured_backend.__class__.__module__ == "keyring.backends.chainer":
            for backend in configured_backend.backends:
                try:
                    _set_password_with_backend(backend, key, passwd)
                    break
                except NotImplementedError:
                    pass
        elif configured_backend is not None and _is_macos_keyring_backend(configured_backend):
            _set_password_with_backend(configured_backend, key, passwd)
        else:
            keyring.set_password("pgcli", key, passwd)
    except Exception as e:
        click.secho(
            keyring_error_message.format("Set password in keyring returned:", str(e)),
            err=True,
            fg="red",
        )
