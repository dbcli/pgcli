from collections import namedtuple

ColumnMetadata = namedtuple('ColumnMetadata', ['name', 'datatype', 'foreignkeys'])
ForeignKey = namedtuple('ForeignKey', ['parentschema', 'parenttable',
    'parentcolumn', 'childschema', 'childtable', 'childcolumn'])
TableMetadata = namedtuple('TableMetadata', 'name columns')


class FunctionMetadata(object):

    def __init__(self, schema_name, func_name, arg_names, arg_types,
        arg_modes, return_type, is_aggregate, is_window, is_set_returning):
        """Class for describing a postgresql function"""

        self.schema_name = schema_name
        self.func_name = func_name

        self.arg_modes = tuple(arg_modes) if arg_modes else None
        self.arg_names = tuple(arg_names) if arg_names else None

        # Be flexible in not requiring arg_types -- use None as a placeholder
        # for each arg. (Used for compatibility with old versions of postgresql
        # where such info is hard to get.
        if arg_types:
            self.arg_types = tuple(arg_types)
        elif arg_modes:
            self.arg_types = tuple([None] * len(arg_modes))
        elif arg_names:
            self.arg_types = tuple([None] * len(arg_names))
        else:
            self.arg_types = None

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
        return hash((self.schema_name, self.func_name, self.arg_names,
            self.arg_types, self.arg_modes, self.return_type,
            self.is_aggregate, self.is_window, self.is_set_returning))

    def __repr__(self):
        return (('%s(schema_name=%r, func_name=%r, arg_names=%r, '
            'arg_types=%r, arg_modes=%r, return_type=%r, is_aggregate=%r, '
            'is_window=%r, is_set_returning=%r)')
                % (self.__class__.__name__, self.schema_name, self.func_name,
                   self.arg_names, self.arg_types, self.arg_modes,
                   self.return_type, self.is_aggregate, self.is_window,
                   self.is_set_returning))

    def fields(self):
        """Returns a list of output-field ColumnMetadata namedtuples"""

        if self.return_type.lower() == 'void':
            return []
        elif not self.arg_modes:
            # For functions  without output parameters, the function name
            # is used as the name of the output column.
            # E.g. 'SELECT unnest FROM unnest(...);'
            return [ColumnMetadata(self.func_name, self.return_type, [])]

        return [ColumnMetadata(name, type, [])
            for name, typ, mode in zip(
                self.arg_names, self.arg_types, self.arg_modes)
            if mode in ('o', 'b', 't')] # OUT, INOUT, TABLE
