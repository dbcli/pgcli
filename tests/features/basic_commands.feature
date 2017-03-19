Feature: run the cli,
  call the help command,
  exit the cli

  Scenario: run the cli
     When we run pgcli
      then we see pgcli prompt

  Scenario: run "\?" command
     When we run pgcli
      and we wait for prompt
      and we send "\?" command
      then we see help output

  Scenario: run the cli and exit
     When we run pgcli
      and we wait for prompt
      and we send "ctrl + d"
      then pgcli exits
