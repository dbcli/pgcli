import shutil
from os.path import expanduser, exists
from configobj import ConfigObj
# from prompt_toolkit.contrib.pdb import set_trace


def load_config(filename, default_filename=None):
    filename = expanduser(filename)
    config = ConfigObj(filename, interpolation=False)

    if default_filename:
        config.merge(load_config(default_filename))

    return config


def write_default_config(source, destination, overwrite=False):
    destination = expanduser(destination)
    if not overwrite and exists(destination):
        return

    shutil.copyfile(source, destination)
