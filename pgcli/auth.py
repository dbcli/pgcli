import click
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
        except Exception as e:  # ImportError for Python 2, ModuleNotFoundError for Python 3
            logger.warning("import keyring failed: %r.", e)


def keyring_get_password(key):
    """Attempt to get password from keyring"""
    # Find password from store
    passwd = ""
    try:
        passwd = keyring.get_password("pgcli", key) or ""
    except Exception as e:
        click.secho(
            keyring_error_message.format(
                "Load your password from keyring returned:", str(e)
            ),
            err=True,
            fg="red",
        )
    return passwd


def keyring_set_password(key, passwd):
    try:
        keyring.set_password("pgcli", key, passwd)
    except Exception as e:
        click.secho(
            keyring_error_message.format("Set password in keyring returned:", str(e)),
            err=True,
            fg="red",
        )
