from shutil import copyfile
from os.path import expanduser, exists
from ConfigParser import SafeConfigParser

def load_config(filename):
    parser = SafeConfigParser()
    parser.read(expanduser(filename))
    return parser

def write_default_config(source, destination, overwrite=False):
    if not overwrite and exists(destination):
        return

    copyfile(source, expanduser(destination))
