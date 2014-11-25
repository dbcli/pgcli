import pyparsing, re, doctest

sqlStyleComment = pyparsing.Literal("--") + pyparsing.ZeroOrMore(pyparsing.CharsNotIn("\n"))
keywords = {'order by': pyparsing.Keyword('order', caseless=True) +
                        pyparsing.Keyword('by', caseless=True),
            'select': pyparsing.Keyword('select', caseless=True),
            'from': pyparsing.Keyword('from', caseless=True),
            'having': pyparsing.Keyword('having', caseless=True),
            'update': pyparsing.Keyword('update', caseless=True),
            'set': pyparsing.Keyword('set', caseless=True),
            'delete': pyparsing.Keyword('delete', caseless=True),
            'insert into': pyparsing.Keyword('insert', caseless=True) +
                           pyparsing.Keyword('into', caseless=True),
            'values': pyparsing.Keyword('values', caseless=True),
            'group by': pyparsing.Keyword('group', caseless=True) +
                        pyparsing.Keyword('by', caseless=True),
            'where': pyparsing.Keyword('where', caseless=True)}
for (name, parser) in keywords.items():
    parser.ignore(pyparsing.sglQuotedString)
    parser.ignore(pyparsing.dblQuotedString)
    parser.ignore(pyparsing.cStyleComment)
    parser.ignore(sqlStyleComment)
    parser.name = name

fromClauseFinder = re.compile(r".*(from|update)(.*)(where|set)",
                    re.IGNORECASE | re.DOTALL | re.MULTILINE)
def tableNamesFromFromClause(statement):
    result = fromClauseFinder.search(statement)
    if not result:
        return []
    result = [r.upper() for r in result if r.upper() not in ('JOIN','ON')]
    return result

def orderedParseResults(parsers, statement):
    results = []
    for parser in parsers:
        results.extend(parser.scanString(statement))
    results.sort(cmp=lambda x,y:cmp(x[1],y[1]))
    return results

at_beginning = re.compile(r'^\s*\S+$')
def whichSegment(statement):
    '''
    >>> whichSegment("SELECT col FROM t")
    'from'
    >>> whichSegment("SELECT * FROM t")
    'from'
    >>> whichSegment("DESC ")
    'DESC'
    >>> whichSegment("DES")
    'beginning'
    >>> whichSegment("")
    'beginning'
    >>> whichSegment("select  ")
    'select'

    '''
    if (not statement) or at_beginning.search(statement):
        return 'beginning'
    results = orderedParseResults(keywords.values(), statement)
    if results:
        return ' '.join(results[-1][0])
    else:
        return statement.split(None,1)[0]

reserved = '''
      access
     add
     all
     alter
     and
     any
     as
     asc
     audit
     between
     by
     char
     check
     cluster
     column
     comment
     compress
     connect
     create
     current
     date
     decimal
     default
     delete
     desc
     distinct
     drop
     else
     exclusive
     exists
     file
     float
     for
     from
     grant
     group
     having
     identified
     immediate
     in
     increment
     index
     initial
     insert
     integer
     intersect
     into
     is
     level
     like
     lock
     long
     maxextents
     minus
     mlslabel
     mode
     modify
     noaudit
     nocompress
     not
     nowait
     null
     number
     of
     offline
     on
     online
     option
     or
     order
     pctfree
     prior
     privileges
     public
     raw
     rename
     resource
     revoke
     row
     rowid
     rownum
     rows
     select
     session
     set
     share
     size
     smallint
     start
     successful
     synonym
     sysdate
     table
     then
     to
     trigger
     uid
     union
     unique
     update
     user
     validate
     values
     varchar
     varchar2
     view
     whenever
     where
     with '''.split()

if __name__ == '__main__':
    doctest.testmod()
