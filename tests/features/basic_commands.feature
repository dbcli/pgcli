Feature: run the cli,
  call the help command,
  exit the cli

  Scenario: run "\?" command
     When we send "\?" command
      then we see help output

  Scenario: run source command
     When we send source command
      then we see help output

  Scenario: run partial select command
     When we send partial select command
       then we see error message
       then we see dbcli prompt

  Scenario: check our application_name
     When we run query to check application_name
      then we see found

  Scenario: run the cli and exit
     When we send "ctrl + d"
      then dbcli exits

  Scenario: list databases
      When we list databases
      then we see list of databases

  Scenario: run the cli with --username
    When we launch dbcli using --username
      and we send "\?" command
      then we see help output

  Scenario: run the cli with --user
    When we launch dbcli using --user
      and we send "\?" command
      then we see help output

  Scenario: run the cli with --port
    When we launch dbcli using --port
      and we send "\?" command
      then we see help output

  Scenario: run the cli with --password
    When we launch dbcli using --password
      then we send password
      and we see dbcli prompt
      when we send "\?" command
      then we see help output

  @wip
  Scenario: run the cli with dsn and password
    When we launch dbcli using dsn_password
      then we send password
      and we see dbcli prompt
      when we send "\?" command
      then we see help output
