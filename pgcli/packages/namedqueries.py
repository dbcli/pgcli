from os.path import expanduser
from ..config import load_config

class NamedQueries:

    section_name = 'named queries'

    def __init__(self, filename):
        self.config = load_config(filename)

    def list(self):
        return self.config.get(self.section_name, [])

    def get(self, name):
        return self.config.get(self.section_name, {}).get(name, None)

    def save(self, name, query):
        if self.section_name not in self.config:
            self.config[self.section_name] = {}
        self.config[self.section_name][name] = query
        self.config.write()

    def delete(self, name):
        if self.section_name in self.config and name in self.config[self.section_name]:
            del self.config[self.section_name][name]
            self.config.write()


namedqueries = NamedQueries('~/.pgclirc')
