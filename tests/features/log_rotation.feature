Feature: log rotation

  Scenario: log rotation by day of week
     When we configure log rotation mode to "day-of-week"
      and we start pgcli
      and we wait for prompt
      and we query "select 1"
      and we wait for prompt
      and we exit pgcli
      then we see a log file named with current day of week

  Scenario: log rotation by day of month
     When we configure log rotation mode to "day-of-month"
      and we start pgcli
      and we wait for prompt
      and we query "select 2"
      and we wait for prompt
      and we exit pgcli
      then we see a log file named with current day of month

  Scenario: log rotation by date
     When we configure log rotation mode to "date"
      and we start pgcli
      and we wait for prompt
      and we query "select 3"
      and we wait for prompt
      and we exit pgcli
      then we see a log file named with current date YYYYMMDD

  Scenario: no log rotation (backwards compatible)
     When we configure log rotation mode to "none"
      and we start pgcli
      and we wait for prompt
      and we query "select 4"
      and we wait for prompt
      and we exit pgcli
      then we see a log file named "pgcli.log"
