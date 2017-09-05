Feature: auto_vertical mode:
  on, off

  Scenario: auto_vertical on with small query
    When we run dbcli with --auto-vertical-output
      and we execute a small query
      then we see small results in horizontal format

  Scenario: auto_vertical on with large query
    When we run dbcli with --auto-vertical-output
      and we execute a large query
      then we see large results in vertical format
