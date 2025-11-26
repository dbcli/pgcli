Feature: run the cli with -y/--yes option,
  force destructive commands without confirmation,
  and exit

  Scenario: run pgcli with --yes and a destructive command
     When we create a test table for destructive tests
      and we run pgcli with --yes and destructive command "ALTER TABLE test_yes_table ADD COLUMN test_col TEXT"
      then we see the command executed without prompt
      and pgcli exits successfully
      and we cleanup the test table

  Scenario: run pgcli with -y and a destructive command
     When we create a test table for destructive tests
      and we run pgcli with -y and destructive command "ALTER TABLE test_yes_table DROP COLUMN IF EXISTS test_col"
      then we see the command executed without prompt
      and pgcli exits successfully
      and we cleanup the test table

  Scenario: run pgcli without --yes and a destructive command in non-interactive mode
     When we create a test table for destructive tests
      and we run pgcli without --yes and destructive command "DROP TABLE test_yes_table"
      then we see the command was not executed
      and we cleanup the test table

  Scenario: run pgcli with --yes and DROP command
     When we create a test table for destructive tests
      and we run pgcli with --yes and destructive command "DROP TABLE test_yes_table"
      then we see the command executed without prompt
      and we see table was dropped
      and pgcli exits successfully

  Scenario: run pgcli with --yes combined with -c option
     When we create a test table for destructive tests
      and we run pgcli with --yes -c "ALTER TABLE test_yes_table ADD COLUMN col1 TEXT" -c "ALTER TABLE test_yes_table ADD COLUMN col2 TEXT"
      then we see both commands executed without prompt
      and pgcli exits successfully
      and we cleanup the test table
