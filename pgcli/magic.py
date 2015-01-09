from pgcli.main import PGCli

def load_ipython_extension(ipython):

    #This is called via the ipython command '%load_ext pgcli.magic'

    #first, load the sql magic if it isn't already loaded
    if not ipython.find_line_magic('sql'):
        ipython.run_line_magic('load_ext', 'sql')

    #register our own magic
    ipython.register_magic_function(pgcli_line_magic, 'line','pgcli')

def pgcli_line_magic(line):

    #for now, assume line is connection string e.g. postgres://localhost
    uri = line

    pgcli = PGCli()
    pgcli.connect_uri(uri)

    try:
        pgcli.run_cli()
    except SystemExit:
        pass

    if not pgcli.query_history:
        return

    q = pgcli.query_history[-1]
    if q.successful:
        ipython = get_ipython()
        return ipython.run_cell_magic('sql', uri, q.query)

