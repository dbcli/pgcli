from shutil import copyfile
from os.path import expanduser, exists
try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:
    from configparser import ConfigParser
# from prompt_toolkit.contrib.pdb import set_trace

def load_config(filename):
    filename = expanduser(filename)
    parser = ConfigParser()
    parser.read(filename)
    return parser

def write_default_config(source, destination, overwrite=False):
    #import pdb; pdb.set_trace()
    #set_trace()
    destination = expanduser(destination)
    if not overwrite and exists(destination):
        return

    copyfile(source, destination)
