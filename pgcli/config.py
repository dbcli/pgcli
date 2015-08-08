import shutil
from os.path import expanduser, exists
from configobj import ConfigObj, ConfigObjError

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

def read_config_files(files, sections, keys, error_logger=None):
    """
    Reads a list of config files and merges them. The last one will win.
    :param files: list of files to read
    :param keys: list of sections to parse
    :param keys: list of keys to retrieve
    :param error_logger: callable to log errors
    :returns: dict, with None for missing keys.
    """
    cnf = ConfigObj()
    for filename in files:
        try:
            cnf.merge(ConfigObj(
                expanduser(filename), interpolation=False))
        except ConfigObjError as e:
            if error_logger:
                assert callable(error_logger)
                error_logger('Error parsing %r.', filename)
                error_logger('Recovering partially parsed config values.')
            cnf.merge(e.config)
            pass

    def get(key):
        result = None
        for sect in sections:
            if sect in cnf and key in cnf[sect]:
                result = cnf[sect][key]
        return result

    return dict([(x, get(x)) for x in keys])
