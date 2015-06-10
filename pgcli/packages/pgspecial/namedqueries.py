class NamedQueries(object):

    section_name = 'named queries'

    def __init__(self, config):
        self.config = config

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

from ...config import load_config
namedqueries = NamedQueries(load_config('~/.pgclirc'))
