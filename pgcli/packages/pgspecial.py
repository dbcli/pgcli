from __future__ import print_function
import sys
import logging
from collections import namedtuple
from .tabulate import tabulate

TableInfo = namedtuple("TableInfo", ['checks', 'relkind', 'hasindex',
'hasrules', 'hastriggers', 'hasoids', 'tablespace', 'reloptions', 'reloftype',
'relpersistence'])


log = logging.getLogger(__name__)

class MockLogging(object):
    def debug(self, string):
        print ("***** Query ******")
        print (string)
        print ("******************")
        print ()

#log = MockLogging()

def parse_special_command(sql):
    command, _, arg = sql.partition(' ')
    verbose = '+' in command
    return (command.strip(), verbose, arg.strip())

def list_schemas(cur, pattern, verbose):
    """
    Returns (rows, headers, status)
    """
    sql = """SELECT n.nspname AS "Name",
    pg_catalog.pg_get_userbyid(n.nspowner) AS "Owner"
    FROM pg_catalog.pg_namespace n WHERE n.nspname """

    if pattern:
        sql += "~ '^(" + pattern.replace('*', '.*') + ")$'"
    else:
        sql += "!~ '^pg_' AND n.nspname <> 'information_schema'"
    sql += " ORDER BY 1;"

    log.debug(sql)
    cur.execute(sql)
    if cur.description:
        headers = [x[0] for x in cur.description]
        return [(cur.fetchall(), headers, cur.statusmessage)]

def describe_table_details(cur, pattern, verbose):
    """
    Returns (rows, headers, status)
    """

    # This is a simple \d command. No table name to follow.
    if not pattern:
        sql = """SELECT n.nspname as "Schema", c.relname as "Name", CASE
        c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN
        'materialized view' WHEN 'i' THEN 'index' WHEN 'S' THEN 'sequence' WHEN
        's' THEN 'special' WHEN 'f' THEN 'foreign table' END as "Type",
        pg_catalog.pg_get_userbyid(c.relowner) as "Owner" FROM
        pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid =
        c.relnamespace WHERE c.relkind IN ('r','v','m','S','f','') AND
        n.nspname <> 'pg_catalog' AND n.nspname <> 'information_schema' AND
        n.nspname !~ '^pg_toast' AND pg_catalog.pg_table_is_visible(c.oid)
        ORDER BY 1,2"""

        log.debug(sql)
        cur.execute(sql)
        if cur.description:
            headers = [x[0] for x in cur.description]
            return [(cur.fetchall(), headers, cur.statusmessage)]

    # This is a \d <tablename> command. A royal pain in the ass.
    sql = '''SELECT c.oid, n.nspname, c.relname FROM pg_catalog.pg_class c LEFT
    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace '''

    schema, relname = sql_name_pattern(pattern)
    if relname:
        sql += ' WHERE c.relname ~ ' + relname
    if schema:
        sql += ' AND n.nspname ~ ' + schema
    sql += ' AND pg_catalog.pg_table_is_visible(c.oid) '
    sql += ' ORDER BY 2,3'
    # Execute the sql, get the results and call describe_one_table_details on each table.

    log.debug(sql)
    cur.execute(sql)
    if not (cur.rowcount > 0):
        return [(None, None, 'Did not find any relation named %s.' % pattern)]

    results = []
    for oid, nspname, relname in cur.fetchall():
        results.append(describe_one_table_details(cur, nspname, relname, oid, verbose))

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
    if (cur.rowcount > 0):
        tableinfo = TableInfo._make(cur.fetchone())
    else:
        return (None, None, 'Did not find any relation with OID %s.' % oid)

    # If it's a seq, fetch it's value and store it for later.
    if tableinfo.relkind == 'S':
        # Do stuff here.
        sql = '''SELECT * FROM "%s"."%s"''' % (schema_name, relation_name)
        log.debug(sql)
        cur.execute(sql)
        if not (cur.rowcount > 0):
            return (None, None, 'Something went wrong.')

        seq_values = cur.fetchone()

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

    view_def = ''
    # /* Check if table is a view or materialized view */
    if ((tableinfo.relkind == 'v' or tableinfo.relkind == 'm') and verbose):
        sql = """SELECT pg_catalog.pg_get_viewdef('%s'::pg_catalog.oid, true)""" % oid
        log.debug(sql)
        cur.execute(sql)
        if cur.rowcount > 0:
            view_def = cur.fetchone()

    # Prepare the cells of the table to print.
    cells = []
    for i, row in enumerate(res):
        cell = []
        cell.append(row[0])   # Column
        cell.append(row[1])   # Type

        if show_modifiers:
            modifier = ''
            if row[5]:
                modifier += ' collate %s' % row[5]
            if row[3]:
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

    status = []
    if (tableinfo.relkind == 'i'):
        # /* Footer information about an index */

        sql = """SELECT i.indisunique, i.indisprimary, i.indisclustered,
        i.indisvalid, (NOT i.indimmediate) AND EXISTS (SELECT 1 FROM
        pg_catalog.pg_constraint WHERE conrelid = i.indrelid AND conindid =
        i.indexrelid AND contype IN ('p','u','x') AND condeferrable) AS
        condeferrable, (NOT i.indimmediate) AND EXISTS (SELECT 1 FROM
        pg_catalog.pg_constraint WHERE conrelid = i.indrelid AND conindid =
        i.indexrelid AND contype IN ('p','u','x') AND condeferred) AS
        condeferred, a.amname, c2.relname, pg_catalog.pg_get_expr(i.indpred,
        i.indrelid, true) FROM pg_catalog.pg_index i, pg_catalog.pg_class c,
        pg_catalog.pg_class c2, pg_catalog.pg_am a WHERE i.indexrelid = c.oid
        AND c.oid = '%s' AND c.relam = a.oid AND i.indrelid = c2.oid;""" % oid

        log.debug(sql)
        cur.execute(sql)

        (indisunique, indisprimary, indisclustered, indisvalid,
        deferrable, deferred, indamname, indtable, indpred) = cur.fetchone()

        if indisprimary:
            status.append("primary key, ")
        elif indisunique:
            status.append("unique, ")
        status.append("%s, " % indamname)

        #/* we assume here that index and table are in same schema */
        status.append('for table "%s.%s"' % (schema_name, indtable))

        if indpred:
            status.append(", predicate (%s)" % indpred)

        if indisclustered:
            status.append(", clustered")

        if indisvalid:
            status.append(", invalid")

        if deferrable:
            status.append(", deferrable")

        if deferred:
            status.append(", initially deferred")

        status.append('\n')
        #add_tablespace_footer(&cont, tableinfo.relkind,
                              #tableinfo.tablespace, true);

    elif tableinfo.relkind == 'S':
        # /* Footer information about a sequence */
        # /* Get the column that owns this sequence */
        sql = ("SELECT pg_catalog.quote_ident(nspname) || '.' ||"
              "\n   pg_catalog.quote_ident(relname) || '.' ||"
                          "\n   pg_catalog.quote_ident(attname)"
                          "\nFROM pg_catalog.pg_class c"
                    "\nINNER JOIN pg_catalog.pg_depend d ON c.oid=d.refobjid"
             "\nINNER JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace"
                          "\nINNER JOIN pg_catalog.pg_attribute a ON ("
                          "\n a.attrelid=c.oid AND"
                          "\n a.attnum=d.refobjsubid)"
               "\nWHERE d.classid='pg_catalog.pg_class'::pg_catalog.regclass"
             "\n AND d.refclassid='pg_catalog.pg_class'::pg_catalog.regclass"
                          "\n AND d.objid=%s \n AND d.deptype='a'" % oid)

        log.debug(sql)
        cur.execute(sql)
        result = cur.fetchone()
        status.append("Owned by: %s" % result[0])

        #/*
         #* If we get no rows back, don't show anything (obviously). We should
         #* never get more than one row back, but if we do, just ignore it and
         #* don't print anything.
         #*/

    elif (tableinfo.relkind == 'r' or tableinfo.relkind == 'm' or
            tableinfo.relkind == 'f'):
        #/* Footer information about a table */

        if (tableinfo.hasindex):
            sql = "SELECT c2.relname, i.indisprimary, i.indisunique, i.indisclustered, "
            sql += "i.indisvalid, "
            sql += "pg_catalog.pg_get_indexdef(i.indexrelid, 0, true),\n  "
            sql += ("pg_catalog.pg_get_constraintdef(con.oid, true), "
                    "contype, condeferrable, condeferred")
            sql += ", c2.reltablespace"
            sql += ("\nFROM pg_catalog.pg_class c, pg_catalog.pg_class c2, "
                    "pg_catalog.pg_index i\n")
            sql += "  LEFT JOIN pg_catalog.pg_constraint con ON (conrelid = i.indrelid AND conindid = i.indexrelid AND contype IN ('p','u','x'))\n"
            sql += ("WHERE c.oid = '%s' AND c.oid = i.indrelid AND i.indexrelid = c2.oid\n"
                    "ORDER BY i.indisprimary DESC, i.indisunique DESC, c2.relname;") % oid

            log.debug(sql)
            result = cur.execute(sql)

            if (cur.rowcount > 0):
                status.append("Indexes:\n")
            for row in cur:

                #/* untranslated index name */
                status.append('    "%s"' % row[0])

                #/* If exclusion constraint, print the constraintdef */
                if row[7] == "x":
                    status.append(row[6])
                else:
                    #/* Label as primary key or unique (but not both) */
                    if row[1]:
                        status.append(" PRIMARY KEY,")
                    elif row[2]:
                        if row[7] == "u":
                            status.append(" UNIQUE CONSTRAINT,")
                        else:
                            status.append(" UNIQUE,")

                    # /* Everything after "USING" is echoed verbatim */
                    indexdef = row[5]
                    usingpos = indexdef.find(" USING ")
                    if (usingpos >= 0):
                        indexdef = indexdef[(usingpos + 7):]
                    status.append(" %s" % indexdef)

                    # /* Need these for deferrable PK/UNIQUE indexes */
                    if row[8]:
                        status.append(" DEFERRABLE")

                    if row[9]:
                        status.append(" INITIALLY DEFERRED")

                # /* Add these for all cases */
                if row[3]:
                    status.append(" CLUSTER")

                if not row[4]:
                    status.append(" INVALID")

                status.append('\n')
                # printTableAddFooter(&cont, buf.data);

                # /* Print tablespace of the index on the same line */
                # add_tablespace_footer(&cont, 'i',
                # atooid(PQgetvalue(result, i, 10)),
                # false);

        # /* print table (and column) check constraints */
        if (tableinfo.checks):
            sql = ("SELECT r.conname, "
                    "pg_catalog.pg_get_constraintdef(r.oid, true)\n"
                    "FROM pg_catalog.pg_constraint r\n"
                    "WHERE r.conrelid = '%s' AND r.contype = 'c'\n"
                    "ORDER BY 1;" % oid)
            log.debug(sql)
            cur.execute(sql)
            if (cur.rowcount > 0):
                status.append("Check constraints:\n")
            for row in cur:
                #/* untranslated contraint name and def */
                status.append("    \"%s\" %s" % row)
            status.append('\n')

        #/* print foreign-key constraints (there are none if no triggers) */
        if (tableinfo.hastriggers):
            sql = ("SELECT conname,\n"
                    " pg_catalog.pg_get_constraintdef(r.oid, true) as condef\n"
                              "FROM pg_catalog.pg_constraint r\n"
                   "WHERE r.conrelid = '%s' AND r.contype = 'f' ORDER BY 1;" %
                   oid)
            log.debug(sql)
            cur.execute(sql)
            if (cur.rowcount > 0):
                status.append("Foreign-key constraints:\n")
            for row in cur:
                #/* untranslated constraint name and def */
                status.append("    \"%s\" %s\n" % row)

        #/* print incoming foreign-key references (none if no triggers) */
        if (tableinfo.hastriggers):
            sql = ("SELECT conname, conrelid::pg_catalog.regclass,\n"
                    "  pg_catalog.pg_get_constraintdef(c.oid, true) as condef\n"
                    "FROM pg_catalog.pg_constraint c\n"
                    "WHERE c.confrelid = '%s' AND c.contype = 'f' ORDER BY 1;" %
                    oid)
            log.debug(sql)
            cur.execute(sql)
            if (cur.rowcount > 0):
                status.append("Referenced by:\n")
            for row in cur:
                status.append("    TABLE \"%s\" CONSTRAINT \"%s\" %s\n" % row)

        # /* print rules */
        if (tableinfo.hasrules and tableinfo.relkind != 'm'):
            sql = ("SELECT r.rulename, trim(trailing ';' from pg_catalog.pg_get_ruledef(r.oid, true)), "
                              "ev_enabled\n"
                              "FROM pg_catalog.pg_rewrite r\n"
                              "WHERE r.ev_class = '%s' ORDER BY 1;" %
                              oid)
            log.debug(sql)
            cur.execute(sql)
            if (cur.rowcount > 0):
                for category in range(4):
                    have_heading = False
                    for row in cur:
                        if category == 0 and row[2] == 'O':
                            list_rule = True
                        elif category == 1 and row[2] == 'D':
                            list_rule = True
                        elif category == 2 and row[2] == 'A':
                            list_rule = True
                        elif category == 3 and row[2] == 'R':
                            list_rule = True

                        if not list_rule:
                            continue

                        if not have_heading:
                            if category == 0:
                                status.append("Rules:")
                            if category == 1:
                                status.append("Disabled rules:")
                            if category == 2:
                                status.append("Rules firing always:")
                            if category == 3:
                                status.append("Rules firing on replica only:")
                            have_heading = True

                        # /* Everything after "CREATE RULE" is echoed verbatim */
                        ruledef = row[1]
                        ruledef += 12
                        status.append("    %s", ruledef)

    if (view_def):
        #/* Footer information about a view */
        status.append("View definition:\n")
        status.append("%s \n" % view_def)

        #/* print rules */
        if tableinfo.hasrules:
            sql = ("SELECT r.rulename, trim(trailing ';' from pg_catalog.pg_get_ruledef(r.oid, true))\n"
                    "FROM pg_catalog.pg_rewrite r\n"
                    "WHERE r.ev_class = '%s' AND r.rulename != '_RETURN' ORDER BY 1;" % oid)

            log.debug(sql)
            cur.execute(sql)
            if (cur.rowcount > 0):
                status.append("Rules:\n")
                for row in cur:
                    #/* Everything after "CREATE RULE" is echoed verbatim */
                    ruledef = row[1]
                    ruledef += 12;

                    status.append(" %s\n", ruledef)


    #/*
    # * Print triggers next, if any (but only user-defined triggers).  This
    # * could apply to either a table or a view.
    # */
    if tableinfo.hastriggers:
        sql = ( "SELECT t.tgname, "
                "pg_catalog.pg_get_triggerdef(t.oid, true), "
                "t.tgenabled\n"
                "FROM pg_catalog.pg_trigger t\n"
                "WHERE t.tgrelid = '%s' AND " % oid);

        sql += "NOT t.tgisinternal"
        sql += "\nORDER BY 1;"

        log.debug(sql)
        cur.execute(sql)
        if cur.rowcount > 0:
            #/*
            #* split the output into 4 different categories. Enabled triggers,
            #* disabled triggers and the two special ALWAYS and REPLICA
            #* configurations.
            #*/
            for category in range(4):
                have_heading = False;
                list_trigger = False;
                for row in cur:
                    #/*
                    # * Check if this trigger falls into the current category
                    # */
                    tgenabled = row[2]
                    if category ==0:
                        if (tgenabled == 'O' or tgenabled == True):
                            list_trigger = True
                    elif category ==1:
                        if (tgenabled == 'D' or tgenabled == False):
                            list_trigger = True
                    elif category ==2:
                        if (tgenabled == 'A'):
                            list_trigger = True
                    elif category ==3:
                        if (tgenabled == 'R'):
                            list_trigger = True
                    if list_trigger == False:
                        continue;

                    # /* Print the category heading once */
                    if not have_heading:
                        if category == 0:
                            status.append("Triggers:")
                        elif category == 1:
                            status.append("Disabled triggers:")
                        elif category == 2:
                            status.append("Triggers firing always:")
                        elif category == 3:
                            status.append("Triggers firing on replica only:")
                        status.append('\n')
                        have_heading = True

                    #/* Everything after "TRIGGER" is echoed verbatim */
                    tgdef = row[1]
                    triggerpos = indexdef.find(" TRIGGER ")
                    if triggerpos >= 0:
                        tgdef = triggerpos + 9;

                    status.append("    %s\n" % tgdef);

    #/*
    #* Finish printing the footer information about a table.
    #*/
    if (tableinfo.relkind == 'r' or tableinfo.relkind == 'm' or
            tableinfo.relkind == 'f'):
        # /* print foreign server name */
        if tableinfo.relkind == 'f':
            #/* Footer information about foreign table */
            sql = ("SELECT s.srvname,\n"
                   "       array_to_string(ARRAY(SELECT "
                   "       quote_ident(option_name) ||  ' ' || "
                   "       quote_literal(option_value)  FROM "
                   "       pg_options_to_table(ftoptions)),  ', ') "
                   "FROM pg_catalog.pg_foreign_table f,\n"
                   "     pg_catalog.pg_foreign_server s\n"
                   "WHERE f.ftrelid = %s AND s.oid = f.ftserver;" % oid)
            log.debug(sql)
            cur.execute(sql)
            row = cur.fetchone()

            # /* Print server name */
            status.append("Server: %s\n" % row[0])

            # /* Print per-table FDW options, if any */
            if (row[1]):
                status.append("FDW Options: (%s)\n" % ftoptions)

        #/* print inherited tables */
        sql = ("SELECT c.oid::pg_catalog.regclass FROM pg_catalog.pg_class c, "
                "pg_catalog.pg_inherits i WHERE c.oid=i.inhparent AND "
                "i.inhrelid = '%s' ORDER BY inhseqno;" % oid)

        log.debug(sql)
        cur.execute(sql)

        spacer = ''
        if cur.rowcount > 0:
            status.append("Inherits")
        for row in cur:
            status.append("%s: %s,\n" % (spacer, row))
            spacer = ' ' * len('Inherits')

        #/* print child tables */
        sql =  ("SELECT c.oid::pg_catalog.regclass FROM pg_catalog.pg_class c,"
            " pg_catalog.pg_inherits i WHERE c.oid=i.inhrelid AND"
            " i.inhparent = '%s' ORDER BY"
            " c.oid::pg_catalog.regclass::pg_catalog.text;" % oid)

        log.debug(sql)
        cur.execute(sql)

        if not verbose:
            #/* print the number of child tables, if any */
            if (cur.rowcount > 0):
                status.append("Number of child tables: %d (Use \d+ to list"
                    "them.)\n" % cur.rowcount)
        else:
            spacer = ''
            if (cur.rowcount >0):
                status.append('Child tables')

            #/* display the list of child tables */
            for row in cur:
                status.append("%s: %s,\n" % (spacer, row))
                spacer = ' ' * len('Child tables')

        #/* Table type */
        if (tableinfo.reloftype):
            status.append("Typed table of type: %s\n" % tableinfo.reloftype)

        #/* OIDs, if verbose and not a materialized view */
        if (verbose and tableinfo.relkind != 'm'):
            status.append("Has OIDs: %s\n" %
                    ("yes" if tableinfo.hasoids else "no"))


        #/* Tablespace info */
        #add_tablespace_footer(&cont, tableinfo.relkind, tableinfo.tablespace,
                              #true);

    # /* reloptions, if verbose */
    if (verbose and tableinfo.reloptions):
        status.append("Options: %s\n" % tableinfo.reloptions)

    return (cells, headers, "".join(status))

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

def show_help(cur, arg, verbose):  # All the parameters are ignored.
    headers = ['Command', 'Description']
    result = []
    for command, value in sorted(CASE_SENSITIVE_COMMANDS.iteritems()):
        if value[1]:
            result.append(value[1])
    return [(result, headers, None)]

def change_db(cur, arg, verbose):
    raise NotImplementedError


CASE_SENSITIVE_COMMANDS = {
            '\?': (show_help, ['\?', 'Help on pgcli commands.']),
            '\c': (change_db, ['\c database_name', 'Connect to a new database.']),
            '\l': ('''SELECT datname FROM pg_database;''', ['\l', 'list databases.']),
            '\d': (describe_table_details, ['\d [pattern]', 'list or describe tables, views and sequences.']),
            '\dn': (list_schemas, ['\dn [pattern]', 'list schemas']),
            '\dt': ('''SELECT n.nspname as "Schema", c.relname as "Name", CASE
            c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN
            'materialized view' WHEN 'i' THEN 'index' WHEN 'S' THEN 'sequence'
            WHEN 's' THEN 'special' WHEN 'f' THEN 'foreign table' END as
            "Type", pg_catalog.pg_get_userbyid(c.relowner) as "Owner" FROM
            pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON n.oid
            = c.relnamespace WHERE c.relkind IN ('r','') AND n.nspname <>
            'pg_catalog' AND n.nspname <> 'information_schema' AND n.nspname !~
            '^pg_toast' AND pg_catalog.pg_table_is_visible(c.oid) ORDER BY
            1,2;''', ['\dt', 'list tables.']),
            '\di': ('''SELECT n.nspname as "Schema", c.relname as "Name", CASE
            c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN
            'materialized view' WHEN 'i' THEN 'index' WHEN 'S' THEN 'sequence'
            WHEN 's' THEN 'special' WHEN 'f' THEN 'foreign table' END as
            "Type", pg_catalog.pg_get_userbyid(c.relowner) as "Owner",
            c2.relname as "Table" FROM pg_catalog.pg_class c LEFT JOIN
            pg_catalog.pg_namespace n ON n.oid = c.relnamespace LEFT JOIN
            pg_catalog.pg_index i ON i.indexrelid = c.oid LEFT JOIN
            pg_catalog.pg_class c2 ON i.indrelid = c2.oid WHERE c.relkind
            IN ('i','') AND n.nspname <> 'pg_catalog' AND
            n.nspname <> 'information_schema' AND n.nspname !~ '^pg_toast'
            AND pg_catalog.pg_table_is_visible(c.oid)
            ORDER BY 1,2;''', ['\di', 'list indexes.']),
            '\dv': ('''SELECT n.nspname as "Schema", c.relname as "Name", CASE
            c.relkind WHEN 'r' THEN 'table' WHEN 'v' THEN 'view' WHEN 'm' THEN
            'materialized view' WHEN 'i' THEN 'index' WHEN 'S' THEN 'sequence'
            WHEN 's' THEN 'special' WHEN 'f' THEN 'foreign table' END as
            "Type", pg_catalog.pg_get_userbyid(c.relowner) as "Owner" FROM
            pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_namespace n ON
            n.oid = c.relnamespace WHERE c.relkind IN ('v','') AND
            n.nspname <> 'pg_catalog' AND n.nspname <> 'information_schema'
            AND n.nspname !~ '^pg_toast' AND
            pg_catalog.pg_table_is_visible(c.oid) ORDER BY 1,2;''',
            ['\dv', 'list views.']),
            }

NON_CASE_SENSITIVE_COMMANDS = {
            'describe': (describe_table_details, ['DESCRIBE [pattern]', '']),
            }

def execute(cur, sql):
    """Execute a special command and return the results. If the special command
    is not supported a KeyError will be raised.
    """
    command, verbose, arg = parse_special_command(sql)

    # Look up the command in the case-sensitive dict, if it's not there look in
    # non-case-sensitive dict. If not there either, throw a KeyError exception.
    global CASE_SENSITIVE_COMMANDS
    global NON_CASE_SENSITIVE_COMMANDS
    try:
        command_executor = CASE_SENSITIVE_COMMANDS[command][0]
    except KeyError:
        command_executor = NON_CASE_SENSITIVE_COMMANDS[command.lower()][0]

    # If the command executor is a function, then call the function with the
    # args. If it's a string, then assume it's an SQL command and run it.
    if callable(command_executor):
        return command_executor(cur, arg, verbose)
    elif isinstance(command_executor, str):
        cur.execute(command_executor)
        if cur.description:
            headers = [x[0] for x in cur.description]
            return [(cur.fetchall(), headers, cur.statusmessage)]
        else:
            return [(None, None, cur.statusmessage)]

if __name__ == '__main__':
    import psycopg2
    con = psycopg2.connect(database='misago_testforum')
    cur = con.cursor()
    table = sys.argv[1]
    for rows, headers, status in describe_table_details(cur, table, False):
        print(tabulate(rows, headers, tablefmt='psql'))
        print(status)
