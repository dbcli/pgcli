from shutil import copyfile
from os.path import expanduser, exists
from ConfigParser import SafeConfigParser

def load_config(filename):
    filename = expanduser(filename)
    parser = SafeConfigParser()
    parser.read(filename)
    return parser

def write_default_config(source, destination, overwrite=False):
    destination = expanduser(destination)
    if not overwrite and exists(destination):
        return

    copyfile(source, destination)
