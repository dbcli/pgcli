Feature: I/O commands

  Scenario: edit sql in file with external editor
     When we start external editor providing a file name
      and we type sql in the editor
      and we exit the editor
      then we see dbcli prompt
      and we see the sql in prompt

  Scenario: tee output from query
     When we tee output
      and we wait for prompt
      and we query "select 123456"
      and we wait for prompt
      and we stop teeing output
      and we wait for prompt
      then we see 123456 in tee output
