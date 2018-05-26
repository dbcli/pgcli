Feature: expanded mode:
  on, off, auto

  Scenario: expanded on
    When we prepare the test data
      and we set expanded on
      and we select from table
      then we see expanded data selected
      when we drop table
      then we confirm the destructive warning
      then we see table dropped

  Scenario: expanded off
    When we prepare the test data
      and we set expanded off
      and we select from table
      then we see nonexpanded data selected
      when we drop table
      then we confirm the destructive warning
      then we see table dropped

  Scenario: expanded auto
    When we prepare the test data
      and we set expanded auto
      and we select from table
      then we see auto data selected
      when we drop table
      then we confirm the destructive warning
      then we see table dropped
