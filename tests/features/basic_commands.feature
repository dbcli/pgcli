Feature: run the cli,
  call the help command,
  exit the cli

  Scenario: run "\?" command
     When we send "\?" command
      then we see help output

  Scenario: run source command
     When we send source command
      then we see help output

  Scenario: run the cli and exit
     When we send "ctrl + d"
      then dbcli exits
