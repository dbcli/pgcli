import re
import sqlparse
from sqlparse.tokens import Whitespace, Comment, Keyword, Name, Punctuation


table_def_regex = re.compile(r'^TABLE\s*\((.+)\)$', re.IGNORECASE)


class FunctionMetadata(object):

    def __init__(self, schema_name, func_name, arg_list, return_type, is_aggregate,
                 is_window, is_set_returning):
        """Class for describing a postgresql function"""

        self.schema_name = schema_name
        self.func_name = func_name
        self.arg_list = arg_list.strip()
        self.return_type = return_type.strip()
        self.is_aggregate = is_aggregate
        self.is_window = is_window
        self.is_set_returning = is_set_returning

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.schema_name, self.func_name, self.arg_list,
                    self.return_type, self.is_aggregate, self.is_window,
                    self.is_set_returning))

    def __repr__(self):
        return (('%s(schema_name=%r, func_name=%r, arg_list=%r, return_type=%r,'
                 ' is_aggregate=%r, is_window=%r, is_set_returning=%r)')
                % (self.__class__.__name__, self.schema_name, self.func_name,
                   self.arg_list, self.return_type, self.is_aggregate,
                   self.is_window, self.is_set_returning))

    def fieldnames(self):
        """Returns a list of output field names"""

        if self.return_type.lower() == 'void':
            return []

        match = table_def_regex.match(self.return_type)
        if match:
            # Function returns a table -- get the column names
            return list(field_names(match.group(1), mode_filter=None))

        # Function may have named output arguments -- find them and return
        # their names
        return list(field_names(self.arg_list, mode_filter=('OUT', 'INOUT')))


class TypedFieldMetadata(object):
    """Describes typed field from a function signature or table definition

        Attributes are:
            name        The name of the argument/column
            mode        'IN', 'OUT', 'INOUT', 'VARIADIC'
            type        A list of tokens denoting the type
            default     A list of tokens denoting the default value
            unknown     A list of tokens not assigned to type or default
    """

    __slots__ = ['name', 'mode', 'type', 'default', 'unknown']

    def __init__(self):
        self.name = None
        self.mode = 'IN'
        self.type = []
        self.default = []
        self.unknown = []

    def __getitem__(self, attr):
        return getattr(self, attr)


def parse_typed_field_list(tokens):
    """Parses a argument/column list, yielding TypedFieldMetadata objects

        Field/column lists are used in function signatures and table
        definitions. This function parses a flattened list of sqlparse tokens
        and yields one metadata argument per argument / column.
    """

    # postgres function argument list syntax:
    #   " ( [ [ argmode ] [ argname ] argtype
    #               [ { DEFAULT | = } default_expr ] [, ...] ] )"

    mode_names = set(('IN', 'OUT', 'INOUT', 'VARIADIC'))
    parse_state = 'type'
    parens = 0
    field = TypedFieldMetadata()

    for tok in tokens:
        if tok.ttype in Whitespace or tok.ttype in Comment:
            continue
        elif tok.ttype in Punctuation:
            if parens == 0 and tok.value == ',':
                # End of the current field specification
                if field.type:
                    yield field
                # Initialize metadata holder for the next field
                field, parse_state = TypedFieldMetadata(), 'type'
            elif parens == 0 and tok.value == '=':
                parse_state = 'default'
            else:
                field[parse_state].append(tok)
                if tok.value == '(':
                    parens += 1
                elif tok.value == ')':
                    parens -= 1
        elif parens == 0:
            if tok.ttype in Keyword:
                if not field.name and tok.value.upper() in mode_names:
                    # No other keywords allowed before arg name
                    field.mode = tok.value.upper()
                elif tok.value.upper() == 'DEFAULT':
                    parse_state = 'default'
                else:
                    parse_state = 'unknown'
            elif tok.ttype == Name and not field.name:
                # note that `ttype in Name` would also match Name.Builtin
                field.name = tok.value
            else:
                field[parse_state].append(tok)
        else:
            field[parse_state].append(tok)

    # Final argument won't be followed by a comma, so make sure it gets yielded
    if field.type:
        yield field


def field_names(sql, mode_filter=('IN', 'OUT', 'INOUT', 'VARIADIC')):
    """Yields field names from a table declaration"""
    # sql is something like "x int, y text, ..."
    tokens = sqlparse.parse(sql)[0].flatten()
    for f in parse_typed_field_list(tokens):
        if f.name and (not mode_filter or f.mode in mode_filter):
            yield f.name




