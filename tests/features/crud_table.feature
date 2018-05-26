Feature: manipulate tables:
  create, insert, update, select, delete from, drop

  Scenario: create, insert, select from, update, drop table
     When we connect to test database
      then we see database connected
      when we create table
      then we see table created
      when we insert into table
      then we see record inserted
      when we update table
      then we see record updated
      when we select from table
      then we see data selected
      when we delete from table
      then we confirm the destructive warning
      then we see record deleted
      when we drop table
      then we confirm the destructive warning
      then we see table dropped
      when we connect to dbserver
      then we see database connected
