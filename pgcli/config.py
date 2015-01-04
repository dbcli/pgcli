import shutil
from os.path import expanduser, exists
try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:
    from configparser import ConfigParser
# from prompt_toolkit.contrib.pdb import set_trace


def load_config(filename, default_filename=None):
    filename = expanduser(filename)
    parser = ConfigParser()

    # parser.read will not fail in case of IOError,
    # so let's not try/except here.
    if default_filename:
        parser.read(default_filename)

    parser.read(filename)
    return parser


def write_default_config(source, destination, overwrite=False):
    destination = expanduser(destination)
    if not overwrite and exists(destination):
        return

    shutil.copyfile(source, destination)
