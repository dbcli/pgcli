Feature: run the cli with -c/--command option,
  execute a single command,
  and exit

  Scenario: run pgcli with -c and a SQL query
     When we run pgcli with -c "SELECT 1 as test_column"
      then we see the query result
      and pgcli exits successfully

  Scenario: run pgcli with --command and a SQL query
     When we run pgcli with --command "SELECT 'hello' as greeting"
      then we see the query result
      and pgcli exits successfully

  Scenario: run pgcli with -c and a special command
     When we run pgcli with -c "\dt"
      then we see the command output
      and pgcli exits successfully

  Scenario: run pgcli with -c and an invalid query
     When we run pgcli with -c "SELECT invalid_column FROM nonexistent_table"
      then we see an error message
      and pgcli exits successfully

  Scenario: run pgcli with -c and multiple statements
     When we run pgcli with -c "SELECT 1; SELECT 2"
      then we see both query results
      and pgcli exits successfully

  Scenario: run pgcli with multiple -c options
     When we run pgcli with multiple -c options
      then we see all command outputs
      and pgcli exits successfully

  Scenario: run pgcli with mixed -c and --command options
     When we run pgcli with mixed -c and --command
      then we see all command outputs
      and pgcli exits successfully
