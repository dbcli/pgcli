import shutil
import os
import platform
from os.path import expanduser, exists
from configobj import ConfigObj

def config_location():
    if platform.system() == 'Windows':
        return os.getenv('USERPROFILE') + '\AppData\Local\dbcli\pgcli\config'
    else:
        return expanduser('~/.config/pgcli/config')

def load_config(usr_cfg, def_cfg=None):
    cfg = ConfigObj()
    cfg.merge(ConfigObj(def_cfg, interpolation=False))
    cfg.merge(ConfigObj(expanduser(usr_cfg), interpolation=False))
    cfg.filename = expanduser(usr_cfg)

    return cfg

def write_default_config(source, destination, overwrite=False):
    destination = expanduser(destination)
    if not overwrite and exists(destination):
        return

    shutil.copyfile(source, destination)

def upgrade_config(config, def_config):
    cfg = load_config(config, def_config)
    cfg.write()
