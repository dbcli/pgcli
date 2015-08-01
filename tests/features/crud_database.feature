Feature: manipulate databases:
  create, drop, connect, disconnect

  Scenario: create and drop temporary database
     Given we have pgcli installed
      when we run pgcli
      and we wait for prompt
      and we create database
      then we see database created
      when we drop database
      then we see database dropped
      when we send "ctrl + d"
      then pgcli exits

  Scenario: connect and disconnect from test database
     Given we have pgcli installed
      when we run pgcli
      and we wait for prompt
      and we connect to test database
      then we see database connected
      when we connect to postgres
      then we see database connected
      when we send "ctrl + d"
      then pgcli exits
