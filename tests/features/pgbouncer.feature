@pgbouncer
Feature: run pgbouncer,
  call the help command,
  exit the cli

  Scenario: run "show help" command
     When we send "show help" command
      then we see the pgbouncer help output

  Scenario: run the cli and exit
     When we send "ctrl + d"
      then dbcli exits
