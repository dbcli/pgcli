from os.path import expanduser
from ..config import load_config

class NamedQueries:

    section_name = 'named queries'
    filename = '~/.pgclirc'

    def __init__(self):
        self.filename = expanduser('~/.pgclirc')
        self.config = load_config(self.filename)

    def list(self):
        if self.config.has_section(self.section_name):
            return self.config.options(self.section_name)
        return []

    def get(self, name):
        if not self.config.has_section(self.section_name):
            return None
        return self.config.get(self.section_name, name)

    def save(self, name, query):
        if not self.config.has_section(self.section_name):
            self.config.add_section(self.section_name)
        self.config.set(self.section_name, name, query)
        self._write()

    def delete(self, name):
        self.config.remove_option(self.section_name, name)
        self._write()

    def _write(self):
        with open(self.filename, 'w') as f:
            self.config.write(f)



namedqueries = NamedQueries()
