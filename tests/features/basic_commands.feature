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

  Scenario: confirm exit when a transaction is ongoing
     When we begin transaction
      and we try to send "ctrl + d"
      then we see ongoing transaction message
      when we send "c"
      then dbcli exits

  Scenario: cancel exit when a transaction is ongoing
     When we begin transaction
      and we try to send "ctrl + d"
      then we see ongoing transaction message
      when we send "a"
      then we see dbcli prompt
      when we rollback transaction
      when we send "ctrl + d"
      then dbcli exits

  Scenario: interrupt current query via "ctrl + c"
     When we send sleep query
      and we send "ctrl + c"
      then we see cancelled query warning
      when we check for any non-idle sleep queries
      then we don't see any non-idle sleep queries

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

  Scenario: run the cli with dsn and password
    When we launch dbcli using dsn_password
      then we send password
      and we see dbcli prompt
      when we send "\?" command
      then we see help output
