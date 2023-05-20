Feature: manipulate tables:
  create, insert, update, select, delete from, drop

  Scenario: create, insert, select from, update, drop table
     When we connect to test database
      then we see database connected
      when we create table
      then we see table created
      when we insert into table
      then we see record inserted
      when we select from table
      then we see data selected: initial
      when we update table
      then we see record updated
      when we select from table
      then we see data selected: updated
      when we delete from table
      then we respond to the destructive warning: y
      then we see record deleted
      when we drop table
      then we respond to the destructive warning: y
      then we see table dropped
      when we connect to dbserver
      then we see database connected

  Scenario: transaction handling, with cancelling on a destructive warning.
    When we connect to test database
      then we see database connected
      when we create table
      then we see table created
      when we begin transaction
      then we see transaction began
      when we insert into table
      then we see record inserted
      when we delete from table
      then we respond to the destructive warning: n
      when we select from table
      then we see data selected: initial
      when we rollback transaction
      then we see transaction rolled back
      when we select from table
      then we see select output without data
      when we drop table
      then we respond to the destructive warning: y
      then we see table dropped
