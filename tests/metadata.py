from pgcli.packages.function_metadata import FunctionMetadata, ForeignKey
from prompt_toolkit.completion import Completion
from functools import partial

escape = lambda name: ('"' + name + '"' if not name.islower() or name in (
    'select', 'insert') else name)

def completion(display_meta, text, pos=0):
    return Completion(text, start_position=pos,
        display_meta=display_meta)

# The code below is quivalent to
# def schema(text, pos=0):
#   return completion('schema', text, pos)
# and so on
schema, table, view, function, column, keyword, datatype, alias, name_join,\
    fk_join, join = [partial(completion, display_meta)
    for display_meta in('schema', 'table', 'view', 'function', 'column',
    'keyword', 'datatype', 'table alias', 'name join', 'fk join', 'join')]

def wildcard_expansion(cols, pos=-1):
        return Completion(cols, start_position=pos, display_meta='columns',
            display = '*')

class MetaData(object):
    def __init__(self, metadata):
        self.metadata = metadata
        self.get_completer()

    def builtin_functions(self, pos=0):
        return [function(f, pos) for f in self.completer.functions]

    def builtin_datatypes(self, pos=0):
        return [datatype(dt, pos) for dt in self.completer.datatypes]

    def keywords(self, pos=0):
        return [keyword(kw, pos) for kw in self.completer.keywords]

    def schemas(self, pos=0):
        schemas = set(sch for schs in self.metadata.values() for sch in schs)
        return [schema(escape(s), pos=pos) for s in schemas]

    def get_completer(self):
        metadata = self.metadata
        import pgcli.pgcompleter as pgcompleter
        self.completer = comp = pgcompleter.PGCompleter(smart_completion=True)

        schemata, tables, tbl_cols, views, view_cols = [], [], [], [], []

        for schema, tbls in metadata['tables'].items():
            schemata.append(schema)

            for table, cols in tbls.items():
                tables.append((schema, table))
                # Let all columns be text columns
                tbl_cols.extend([(schema, table, col, 'text') for col in cols])

        for schema, tbls in metadata.get('views', {}).items():
            for view, cols in tbls.items():
                views.append((schema, view))
                # Let all columns be text columns
                view_cols.extend([(schema, view, col, 'text') for col in cols])

        functions = [FunctionMetadata(schema, *func_meta)
                        for schema, funcs in metadata['functions'].items()
                        for func_meta in funcs]

        datatypes = [(schema, datatype)
                        for schema, datatypes in metadata['datatypes'].items()
                        for datatype in datatypes]

        foreignkeys = [ForeignKey(*fk) for fks in metadata['foreignkeys'].values()
            for fk in fks]

        comp.extend_schemata(schemata)
        comp.extend_relations(tables, kind='tables')
        comp.extend_relations(views, kind='views')
        comp.extend_columns(tbl_cols, kind='tables')
        comp.extend_columns(view_cols, kind='views')
        comp.extend_functions(functions)
        comp.extend_datatypes(datatypes)
        comp.extend_foreignkeys(foreignkeys)
        comp.set_search_path(['public'])
