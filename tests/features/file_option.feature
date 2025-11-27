Feature: run the cli with -f/--file option,
  execute commands from file,
  and exit

  Scenario: run pgcli with -f and a SQL query file
     When we create a file with "SELECT 1 as test_diego_column"
      and we run pgcli with -f and the file
     then we see the query result
      and pgcli exits successfully

  Scenario: run pgcli with --file and a SQL query file
     When we create a file with "SELECT 'hello' as greeting"
      and we run pgcli with --file and the file
     then we see the query result
      and pgcli exits successfully

  Scenario: run pgcli with -f and a file with special command
     When we create a file with "\dt"
      and we run pgcli with -f and the file
     then we see the command output
      and pgcli exits successfully

  Scenario: run pgcli with -f and a file with multiple statements
     When we create a file with "SELECT 1; SELECT 2"
      and we run pgcli with -f and the file
     then we see both query results
      and pgcli exits successfully

  Scenario: run pgcli with -f and a file with an invalid query
     When we create a file with "SELECT invalid_column FROM nonexistent_table"
      and we run pgcli with -f and the file
     then we see an error message
      and pgcli exits successfully

  Scenario: run pgcli with both -c and -f options
     When we create a file with "SELECT 2 as second"
      and we run pgcli with -c "SELECT 1 as first" and -f with the file
     then we see both query results
      and pgcli exits successfully
