from functools import partial
from itertools import product
from pgcli.packages.parseutils.meta import FunctionMetadata, ForeignKey
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
from mock import Mock
import pytest

parametrize = pytest.mark.parametrize

qual = ["if_more_than_one_table", "always"]
no_qual = ["if_more_than_one_table", "never"]


def escape(name):
    if not name.islower() or name in ("select", "localtimestamp"):
        return '"' + name + '"'
    return name


def completion(display_meta, text, pos=0):
    return Completion(text, start_position=pos, display_meta=display_meta)


def function(text, pos=0, display=None):
    return Completion(
        text, display=display or text, start_position=pos, display_meta="function"
    )


def get_result(completer, text, position=None):
    position = len(text) if position is None else position
    return completer.get_completions(
        Document(text=text, cursor_position=position), Mock()
    )


def result_set(completer, text, position=None):
    return set(get_result(completer, text, position))


# The code below is quivalent to
# def schema(text, pos=0):
#   return completion('schema', text, pos)
# and so on
schema = partial(completion, "schema")
table = partial(completion, "table")
view = partial(completion, "view")
column = partial(completion, "column")
keyword = partial(completion, "keyword")
datatype = partial(completion, "datatype")
alias = partial(completion, "table alias")
name_join = partial(completion, "name join")
fk_join = partial(completion, "fk join")
join = partial(completion, "join")


def wildcard_expansion(cols, pos=-1):
    return Completion(cols, start_position=pos, display_meta="columns", display="*")


class MetaData(object):
    def __init__(self, metadata):
        self.metadata = metadata

    def builtin_functions(self, pos=0):
        return [function(f, pos) for f in self.completer.functions]

    def builtin_datatypes(self, pos=0):
        return [datatype(dt, pos) for dt in self.completer.datatypes]

    def keywords(self, pos=0):
        return [keyword(kw, pos) for kw in self.completer.keywords_tree.keys()]

    def specials(self, pos=0):
        return [
            Completion(text=k, start_position=pos, display_meta=v.description)
            for k, v in self.completer.pgspecial.commands.items()
        ]

    def columns(self, tbl, parent="public", typ="tables", pos=0):
        if typ == "functions":
            fun = [x for x in self.metadata[typ][parent] if x[0] == tbl][0]
            cols = fun[1]
        else:
            cols = self.metadata[typ][parent][tbl]
        return [column(escape(col), pos) for col in cols]

    def datatypes(self, parent="public", pos=0):
        return [
            datatype(escape(x), pos)
            for x in self.metadata.get("datatypes", {}).get(parent, [])
        ]

    def tables(self, parent="public", pos=0):
        return [
            table(escape(x), pos)
            for x in self.metadata.get("tables", {}).get(parent, [])
        ]

    def views(self, parent="public", pos=0):
        return [
            view(escape(x), pos) for x in self.metadata.get("views", {}).get(parent, [])
        ]

    def functions(self, parent="public", pos=0):
        return [
            function(
                escape(x[0])
                + "("
                + ", ".join(
                    arg_name + " := "
                    for (arg_name, arg_mode) in zip(x[1], x[3])
                    if arg_mode in ("b", "i")
                )
                + ")",
                pos,
                escape(x[0])
                + "("
                + ", ".join(
                    arg_name
                    for (arg_name, arg_mode) in zip(x[1], x[3])
                    if arg_mode in ("b", "i")
                )
                + ")",
            )
            for x in self.metadata.get("functions", {}).get(parent, [])
        ]

    def schemas(self, pos=0):
        schemas = set(sch for schs in self.metadata.values() for sch in schs)
        return [schema(escape(s), pos=pos) for s in schemas]

    def functions_and_keywords(self, parent="public", pos=0):
        return (
            self.functions(parent, pos)
            + self.builtin_functions(pos)
            + self.keywords(pos)
        )

    # Note that the filtering parameters here only apply to the columns
    def columns_functions_and_keywords(self, tbl, parent="public", typ="tables", pos=0):
        return self.functions_and_keywords(pos=pos) + self.columns(
            tbl, parent, typ, pos
        )

    def from_clause_items(self, parent="public", pos=0):
        return (
            self.functions(parent, pos)
            + self.views(parent, pos)
            + self.tables(parent, pos)
        )

    def schemas_and_from_clause_items(self, parent="public", pos=0):
        return self.from_clause_items(parent, pos) + self.schemas(pos)

    def types(self, parent="public", pos=0):
        return self.datatypes(parent, pos) + self.tables(parent, pos)

    @property
    def completer(self):
        return self.get_completer()

    def get_completers(self, casing):
        """
        Returns a function taking three bools `casing`, `filtr`, `aliasing` and
        the list `qualify`, all defaulting to None.
        Returns a list of completers.
        These parameters specify the allowed values for the corresponding
        completer parameters, `None` meaning any, i.e. (None, None, None, None)
        results in all 24 possible completers, whereas e.g.
        (True, False, True, ['never']) results in the one completer with
        casing, without `search_path` filtering of objects, with table
        aliasing, and without column qualification.
        """

        def _cfg(_casing, filtr, aliasing, qualify):
            cfg = {"settings": {}}
            if _casing:
                cfg["casing"] = casing
            cfg["settings"]["search_path_filter"] = filtr
            cfg["settings"]["generate_aliases"] = aliasing
            cfg["settings"]["qualify_columns"] = qualify
            return cfg

        def _cfgs(casing, filtr, aliasing, qualify):
            casings = [True, False] if casing is None else [casing]
            filtrs = [True, False] if filtr is None else [filtr]
            aliases = [True, False] if aliasing is None else [aliasing]
            qualifys = qualify or ["always", "if_more_than_one_table", "never"]
            return [_cfg(*p) for p in product(casings, filtrs, aliases, qualifys)]

        def completers(casing=None, filtr=None, aliasing=None, qualify=None):
            get_comp = self.get_completer
            return [get_comp(**c) for c in _cfgs(casing, filtr, aliasing, qualify)]

        return completers

    def _make_col(self, sch, tbl, col):
        defaults = self.metadata.get("defaults", {}).get(sch, {})
        return (sch, tbl, col, "text", (tbl, col) in defaults, defaults.get((tbl, col)))

    def get_completer(self, settings=None, casing=None):
        metadata = self.metadata
        from pgcli.pgcompleter import PGCompleter
        from pgspecial import PGSpecial

        comp = PGCompleter(
            smart_completion=True, settings=settings, pgspecial=PGSpecial()
        )

        schemata, tables, tbl_cols, views, view_cols = [], [], [], [], []

        for sch, tbls in metadata["tables"].items():
            schemata.append(sch)

            for tbl, cols in tbls.items():
                tables.append((sch, tbl))
                # Let all columns be text columns
                tbl_cols.extend([self._make_col(sch, tbl, col) for col in cols])

        for sch, tbls in metadata.get("views", {}).items():
            for tbl, cols in tbls.items():
                views.append((sch, tbl))
                # Let all columns be text columns
                view_cols.extend([self._make_col(sch, tbl, col) for col in cols])

        functions = [
            FunctionMetadata(sch, *func_meta, arg_defaults=None)
            for sch, funcs in metadata["functions"].items()
            for func_meta in funcs
        ]

        datatypes = [
            (sch, typ)
            for sch, datatypes in metadata["datatypes"].items()
            for typ in datatypes
        ]

        foreignkeys = [
            ForeignKey(*fk) for fks in metadata["foreignkeys"].values() for fk in fks
        ]

        comp.extend_schemata(schemata)
        comp.extend_relations(tables, kind="tables")
        comp.extend_relations(views, kind="views")
        comp.extend_columns(tbl_cols, kind="tables")
        comp.extend_columns(view_cols, kind="views")
        comp.extend_functions(functions)
        comp.extend_datatypes(datatypes)
        comp.extend_foreignkeys(foreignkeys)
        comp.set_search_path(["public"])
        comp.extend_casing(casing or [])

        return comp
