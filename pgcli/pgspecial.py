#import logging
from collections import namedtuple

commands = {
            '\d': '''SELECT n.nspname as "Schema", c.relname as "Name", CASE c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized view' WHEN 'i' THEN 'index' WHEN 'S' THEN 'sequence' WHEN 's' THEN 'special' WHEN 'f' THEN 'foreign table' END as "Type", pg_catalog.pg_get_userbyid(c.relowner) as "Owner" FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r','v','m','S','f','') AND n.nspname <> 'pg_catalog' AND n.nspname <> 'information_schema' AND n.nspname !~ '^pg_toast' AND pg_catalog.pg_table_is_visible(c.oid) ORDER BY 1,2;''',
            '\dt': '''SELECT n.nspname as "Schema", c.relname as "Name", CASE c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN 'materialized view' WHEN 'i' THEN 'index' WHEN 'S' THEN 'sequence' WHEN 's' THEN 'special' WHEN 'f' THEN 'foreign table' END as "Type", pg_catalog.pg_get_userbyid(c.relowner) as "Owner" FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r','') AND n.nspname <> 'pg_catalog' AND n.nspname <> 'information_schema' AND n.nspname !~ '^pg_toast' AND pg_catalog.pg_table_is_visible(c.oid) ORDER BY 1,2;'''
        }

TableInfo = namedtuple("TableInfo", ['checks', 'relkind', 'hasindex',
'hasrules', 'hastriggers', 'hasoids', 'tablespace', 'reloptions', 'reloftype',
'relpersistence'])


#log = logging.get(__name__)

class MockLogging(object):
    def debug(self, string):
        print "*****Query******"
        print string
        print "****************"

log = MockLogging()

def describe_table_details(cur, pattern, verbose):
    """
    Returns (rows, headers, status)
    """

    sql = '''SELECT c.oid, n.nspname, c.relname FROM pg_catalog.pg_class c LEFT
    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace '''

    if pattern:
        schema, relname = sql_name_pattern(pattern)
        if relname:
            sql += ' WHERE c.relname ~ ' + relname
        if schema:
            sql += ' AND n.nspname ~ ' + schema
        sql += ' AND pg_catalog.pg_table_is_visible(c.oid) '
    else:
        sql += """WHERE n.nspname <> 'pg_catalog'
        AND n.nspname <> 'information_schema'"""

    sql += ' ORDER BY 2,3'

    # Execute the sql, get the results and call describe_one_table_details on each table.

    log.debug(sql)
    cur.execute(sql)
    if not cur.description:
        return None, None, 'Did not find any relation named %s.' % pattern

    results = []
    for oid, nspname, relname in cur.fetchall():
        results.append( describe_one_table_details(cur, nspname, relname, oid, verbose))

    return results

def describe_one_table_details(cur, schema_name, relation_name, oid, verbose):
    if verbose:
        suffix = """pg_catalog.array_to_string(c.reloptions || array(select
        'toast.' || x from pg_catalog.unnest(tc.reloptions) x), ', ')"""
    else:
        suffix = "''"

    sql = """SELECT c.relchecks, c.relkind, c.relhasindex, c.relhasrules,
    c.relhastriggers, c.relhasoids, %s, c.reltablespace, CASE WHEN c.reloftype
    = 0 THEN '' ELSE c.reloftype::pg_catalog.regtype::pg_catalog.text END,
    c.relpersistence FROM pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_class
    tc ON (c.reltoastrelid = tc.oid) WHERE c.oid = '%s'""" % (suffix, oid)

    # Create a namedtuple called tableinfo and match what's in describe.c

    log.debug(sql)
    cur.execute(sql)
    if cur.description:
        tableinfo = TableInfo._make(cur.fetchone())
    else:
        return None, None, 'Did not find any relation with OID %s.' % oid

    # If it's a seq, fetch it's value and store it for later.
    if tableinfo.relkind == 'S':
        # Do stuff here.
        sql = """SELECT * FROM '%s'.'%s'""" % (schema_name, relation_name)
        log.debug(sql)
        cur.execute(sql)
        if not cur.description:
            return None, None, 'Something went wrong.'

        seq_values = cur.fetchall()

    # Get column info
    sql = """
        SELECT a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod),
        (SELECT substring(pg_catalog.pg_get_expr(d.adbin, d.adrelid) for 128)
        FROM pg_catalog.pg_attrdef d WHERE d.adrelid = a.attrelid AND d.adnum =
        a.attnum AND a.atthasdef), a.attnotnull, a.attnum, (SELECT c.collname
        FROM pg_catalog.pg_collation c, pg_catalog.pg_type t WHERE c.oid =
        a.attcollation AND t.oid = a.atttypid AND a.attcollation <>
        t.typcollation) AS attcollation"""

    if tableinfo.relkind == 'i':
        sql += """, pg_catalog.pg_get_indexdef(a.attrelid, a.attnum, TRUE)
                AS indexdef"""
    else:
        sql += """, NULL AS indexdef"""

    if tableinfo.relkind == 'f':
        sql += """, CASE WHEN attfdwoptions IS NULL THEN '' ELSE '(' ||
                array_to_string(ARRAY(SELECT quote_ident(option_name) ||  ' '
                || quote_literal(option_value)  FROM
                pg_options_to_table(attfdwoptions)), ', ') || ')' END AS
        attfdwoptions"""
    else:
        sql += """, NULL AS attfdwoptions"""

    if verbose:
        sql += """, a.attstorage"""
        sql += """, CASE WHEN a.attstattarget=-1 THEN NULL ELSE
                a.attstattarget END AS attstattarget"""
        if (tableinfo.relkind == 'r' or tableinfo.relkind == 'v' or
                tableinfo.relkind == 'm' or tableinfo.relkind == 'f' or
                tableinfo.relkind == 'c'):
            sql += """, pg_catalog.col_description(a.attrelid,
                    a.attnum)"""

    sql += """ FROM pg_catalog.pg_attribute a WHERE a.attrelid = '%s' AND
    a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum; """ % oid

    log.debug(sql)
    cur.execute(sql)
    res = cur.fetchall()

    title = (tableinfo.relkind, schema_name, relation_name)

    # Set the column names.
    headers = ['Column', 'Type']

    show_modifiers = False
    if (tableinfo.relkind == 'r' or tableinfo.relkind == 'v' or
            tableinfo.relkind == 'm' or tableinfo.relkind == 'f' or
            tableinfo.relkind == 'c'):
        headers.append('Modifiers')
        show_modifiers = True

    if (tableinfo.relkind == 'S'):
            headers.append("Value")

    if (tableinfo.relkind == 'i'):
            headers.append("Definition")

    if (tableinfo.relkind == 'f'):
            headers.append("FDW Options")

    if (verbose):
        headers.append("Storage")
        if (tableinfo.relkind == 'r' or tableinfo.relkind == 'm' or
                tableinfo.relkind == 'f'):
            headers.append("Stats target")
        #  Column comments, if the relkind supports this feature. */
        if (tableinfo.relkind == 'r' or tableinfo.relkind == 'v' or
                tableinfo.relkind == 'm' or
                tableinfo.relkind == 'c' or tableinfo.relkind == 'f'):
            headers.append("Description")

    # /* Check if table is a view or materialized view */
    if ((tableinfo.relkind == 'v' or tableinfo.relkind == 'm') and verbose):
        sql = """SELECT pg_catalog.pg_get_viewdef('%s'::pg_catalog.oid, true)""" % oid
        cur.execute(sql)
        view_def = cur.fetchone()

    # Perpare the cells of the table to print.
    cells = []
    for i, row in enumerate(res):
        cell = []
        cell.append(row[0])   # Column
        cell.append(row[1])   # Type

        if show_modifiers:
            modifier = ''
            if row[5]:
                modifier += ' collate %s' % row[5]
            if row[3] == 't':
                modifier += ' not null'
            if row[2]:
                modifier += ' default %s' % row[2]

            cell.append(modifier)

        # Sequence
        if tableinfo.relkind == 'S':
            cell.append(seq_values[i])

        # Index column
        if TableInfo.relkind == 'i':
            cell.append(row[6])

        # /* FDW options for foreign table column, only for 9.2 or later */
        if tableinfo.relkind == 'f':
            cell.append(row[7])

        if verbose:
            storage = row[8]

            if storage[0] == 'p':
                cell.append('plain')
            elif storage[0] == 'm':
                cell.append('main')
            elif storage[0] == 'x':
                cell.append('extended')
            elif storage[0] == 'e':
                cell.append('external')
            else:
                cell.append('???')

            if (tableinfo.relkind == 'r' or tableinfo.relkind == 'm' or
                    tableinfo.relkind == 'f'):
                cell.append(row[9])

            #  /* Column comments, if the relkind supports this feature. */
            if (tableinfo.relkind == 'r' or tableinfo.relkind == 'v' or
                    tableinfo.relkind == 'm' or
                    tableinfo.relkind == 'c' or tableinfo.relkind == 'f'):
                cell.append(row[10])
        cells.append(cell)

    # Make Footers

    return cells, headers, "blah"

def sql_name_pattern(pattern):
    """
    Takes a wildcard-pattern and converts to an appropriate SQL pattern to be
    used in a WHERE clause.

    Returns: schema_pattern, table_pattern
    """

    def replacements(pattern):
        result = pattern.replace('*', '.*')
        result = result.replace('?', '.')
        result = result.replace('$', '\\$')
        return result

    schema, _, relname = pattern.rpartition('.')
    if schema:
        schema = "'^(" + replacements(schema) + ")$'"
    if relname:
        relname = "'^(" + replacements(relname) + ")$'"

    return schema, relname


if __name__ == '__main__':
    import psycopg2
    con = psycopg2.connect(database='misago_testforum')
    cur = con.cursor()
    #print describe_table_details(cur, 'django_migrations', False)
    print describe_table_details(cur, None, False)
