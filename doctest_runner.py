if __name__ == '__main__':
    import doctest
    import pgcli.pgexecute
    doctest.testmod(pgcli.pgexecute)
    import pgcli.packages.sqlcompletion
    doctest.testmod(pgcli.packages.sqlcompletion)
