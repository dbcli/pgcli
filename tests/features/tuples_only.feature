Feature: run the cli with -t/--tuples-only option,
  print rows only without status messages and timing

  Scenario: run pgcli with -t flag (default csv-noheader format)
     When we run pgcli with "-t -c 'SELECT 1'"
      then we see only the data rows
      and we don't see "SELECT"
      and we don't see "Time:"
      and pgcli exits successfully

  Scenario: run pgcli with --tuples-only flag
     When we run pgcli with "--tuples-only -c 'SELECT 1'"
      then we see only the data rows
      and we don't see "SELECT"
      and we don't see "Time:"
      and pgcli exits successfully

  Scenario: run pgcli with -t and minimal format
     When we run pgcli with "-t minimal -c 'SELECT 1, 2'"
      then we see only the data rows
      and we don't see "SELECT"
      and we don't see "Time:"
      and pgcli exits successfully

  Scenario: run pgcli with -t and tsv_noheader format
     When we run pgcli with "-t tsv_noheader -c 'SELECT 1, 2'"
      then we see tab-separated values
      and we don't see "SELECT"
      and we don't see "Time:"
      and pgcli exits successfully

  Scenario: run pgcli without -t flag (normal output)
     When we run pgcli with "-c 'SELECT 1'"
      then we see "SELECT" in the output
      and we see "Time:" in the output
      and pgcli exits successfully

  Scenario: run pgcli with -t and multiple rows
     When we run pgcli with "-t -c 'SELECT generate_series(1, 3)'"
      then we see multiple data rows
      and we don't see "SELECT"
      and we don't see "Time:"
      and pgcli exits successfully

  Scenario: run pgcli with -t and special command
     When we run pgcli with "-t -c '\\dt'"
      then we see the command output
      and pgcli exits successfully
