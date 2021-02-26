import errno
import shutil
import os
import platform
from os.path import expanduser, exists, dirname
import re
from typing import TextIO
from configobj import ConfigObj


def config_location():
    if "XDG_CONFIG_HOME" in os.environ:
        return "%s/pgcli/" % expanduser(os.environ["XDG_CONFIG_HOME"])
    elif platform.system() == "Windows":
        return os.getenv("USERPROFILE") + "\\AppData\\Local\\dbcli\\pgcli\\"
    else:
        return expanduser("~/.config/pgcli/")


def load_config(usr_cfg, def_cfg=None):
    # avoid config merges when possible. For writing, we need an umerged config instance.
    # see https://github.com/dbcli/pgcli/issues/1240 and https://github.com/DiffSK/configobj/issues/171
    if def_cfg:
        cfg = ConfigObj()
        cfg.merge(ConfigObj(def_cfg, interpolation=False))
        cfg.merge(ConfigObj(expanduser(usr_cfg), interpolation=False, encoding="utf-8"))
    else:
        cfg = ConfigObj(expanduser(usr_cfg), interpolation=False, encoding="utf-8")
    cfg.filename = expanduser(usr_cfg)
    return cfg


def ensure_dir_exists(path):
    parent_dir = expanduser(dirname(path))
    os.makedirs(parent_dir, exist_ok=True)


def write_default_config(source, destination, overwrite=False):
    destination = expanduser(destination)
    if not overwrite and exists(destination):
        return

    ensure_dir_exists(destination)

    shutil.copyfile(source, destination)


def upgrade_config(config, def_config):
    cfg = load_config(config, def_config)
    cfg.write()


def get_config_filename(pgclirc_file=None):
    return pgclirc_file or "%sconfig" % config_location()


def get_config(pgclirc_file=None):
    from pgcli import __file__ as package_root

    package_root = os.path.dirname(package_root)

    pgclirc_file = get_config_filename(pgclirc_file)

    default_config = os.path.join(package_root, "pgclirc")
    write_default_config(default_config, pgclirc_file)

    return load_config(pgclirc_file, default_config)


def get_casing_file(config):
    casing_file = config["main"]["casing_file"]
    if casing_file == "default":
        casing_file = config_location() + "casing"
    return casing_file


def skip_initial_comment(f_stream: TextIO) -> int:
    """
    Initial comment in ~/.pg_service.conf is not always marked with '#'
    which crashes the parser. This function takes a file object and
    "rewinds" it to the beginning of the first section,
    from where on it can be parsed safely

    :return: number of skipped lines
    """
    section_regex = r"\s*\["
    pos = f_stream.tell()
    lines_skipped = 0
    while True:
        line = f_stream.readline()
        if line == "":
            break
        if re.match(section_regex, line) is not None:
            f_stream.seek(pos)
            break
        else:
            pos += len(line)
            lines_skipped += 1
    return lines_skipped
