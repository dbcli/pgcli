from __future__ import print_function
import sqlparse
from collections import namedtuple
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML, Punctuation

TableReference = namedtuple('TableReference', ['schema', 'name', 'alias',
                                               'is_function'])
TableReference.ref = property(lambda self: self.alias or (
  self.name if self.name.islower() or self.name[0] == '"'
  else '"' + self.name + '"'))


# This code is borrowed from sqlparse example script.
# <url>
def is_subselect(parsed):
    if not parsed.is_group:
        return False
    for item in parsed.tokens:
        if item.ttype is DML and item.value.upper() in ('SELECT', 'INSERT',
                'UPDATE', 'CREATE', 'DELETE'):
            return True
    return False


def _identifier_is_function(identifier):
    return any(isinstance(t, Function) for t in identifier.tokens)


def extract_from_part(parsed, stop_at_punctuation=True):
    tbl_prefix_seen = False
    for item in parsed.tokens:
        if tbl_prefix_seen:
            if is_subselect(item):
                for x in extract_from_part(item, stop_at_punctuation):
                    yield x
            elif stop_at_punctuation and item.ttype is Punctuation:
                raise StopIteration
            # An incomplete nested select won't be recognized correctly as a
            # sub-select. eg: 'SELECT * FROM (SELECT id FROM user'. This causes
            # the second FROM to trigger this elif condition resulting in a
            # StopIteration. So we need to ignore the keyword if the keyword
            # FROM.
            # Also 'SELECT * FROM abc JOIN def' will trigger this elif
            # condition. So we need to ignore the keyword JOIN and its variants
            # INNER JOIN, FULL OUTER JOIN, etc.
            elif item.ttype is Keyword and (
                    not item.value.upper() == 'FROM') and (
                    not item.value.upper().endswith('JOIN')):
                tbl_prefix_seen = False
            else:
                yield item
        elif item.ttype is Keyword or item.ttype is Keyword.DML:
            item_val = item.value.upper()
            if (item_val in ('COPY', 'FROM', 'INTO', 'UPDATE', 'TABLE') or
                    item_val.endswith('JOIN')):
                tbl_prefix_seen = True
        # 'SELECT a, FROM abc' will detect FROM as part of the column list.
        # So this check here is necessary.
        elif isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                if (identifier.ttype is Keyword and
                        identifier.value.upper() == 'FROM'):
                    tbl_prefix_seen = True
                    break


def extract_table_identifiers(token_stream, allow_functions=True):
    """yields tuples of TableReference namedtuples"""

    # We need to do some massaging of the names because postgres is case-
    # insensitive and '"Foo"' is not the same table as 'Foo' (while 'foo' is)
    def parse_identifier(item):
        name = item.get_real_name()
        schema_name = item.get_parent_name()
        alias = item.get_alias()
        if not name:
            schema_name = None
            name = item.get_name()
            alias = alias or name
        schema_quoted = schema_name and item.value[0] == '"'
        if schema_name and not schema_quoted:
            schema_name = schema_name.lower()
        quote_count = item.value.count('"')
        name_quoted = quote_count > 2 or (quote_count and not schema_quoted)
        alias_quoted = alias and item.value[-1] == '"'
        if alias_quoted or name_quoted and not alias and name.islower():
            alias = '"' + (alias or name) + '"'
        if name and not name_quoted and not name.islower():
            if not alias:
                alias = name
            name = name.lower()
        return schema_name, name, alias


    for item in token_stream:
        if isinstance(item, IdentifierList):
            for identifier in item.get_identifiers():
                # Sometimes Keywords (such as FROM ) are classified as
                # identifiers which don't have the get_real_name() method.
                try:
                    schema_name = identifier.get_parent_name()
                    real_name = identifier.get_real_name()
                    is_function = (allow_functions and
                                   _identifier_is_function(identifier))
                except AttributeError:
                    continue
                if real_name:
                    yield TableReference(schema_name, real_name,
                                         identifier.get_alias(), is_function)
        elif isinstance(item, Identifier):
            schema_name, real_name, alias = parse_identifier(item)
            is_function = allow_functions and _identifier_is_function(item)

            yield TableReference(schema_name, real_name, alias, is_function)
        elif isinstance(item, Function):
            schema_name, real_name, alias = parse_identifier(item)
            yield TableReference(None, real_name, alias, allow_functions)


# extract_tables is inspired from examples in the sqlparse lib.
def extract_tables(sql):
    """Extract the table names from an SQL statment.

    Returns a list of TableReference namedtuples

    """
    parsed = sqlparse.parse(sql)
    if not parsed:
        return ()

    # INSERT statements must stop looking for tables at the sign of first
    # Punctuation. eg: INSERT INTO abc (col1, col2) VALUES (1, 2)
    # abc is the table name, but if we don't stop at the first lparen, then
    # we'll identify abc, col1 and col2 as table names.
    insert_stmt = parsed[0].token_first().value.lower() == 'insert'
    stream = extract_from_part(parsed[0], stop_at_punctuation=insert_stmt)

    # Kludge: sqlparse mistakenly identifies insert statements as
    # function calls due to the parenthesized column list, e.g. interprets
    # "insert into foo (bar, baz)" as a function call to foo with arguments
    # (bar, baz). So don't allow any identifiers in insert statements
    # to have is_function=True
    identifiers = extract_table_identifiers(stream,
                                            allow_functions=not insert_stmt)
    # In the case 'sche.<cursor>', we get an empty TableReference; remove that
    return tuple(i for i in identifiers if i.name)


def schema_table_split(spec):
    """ "myschema.mytable" -> ('myschema', 'mytable); "mytable" -> (None, 'mytable')"""

    pieces = spec.strip().split('.')
    if len(pieces) == 1:
        return ('%', pieces[0])
    else:
        return (pieces[0], '.'.join(pieces[1:]))
