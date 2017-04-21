Feature: Special commands

  @wip
  Scenario: run refresh command
     When we run dbcli
      and we wait for prompt
      and we refresh completions
      and we wait for prompt
      then we see completions refresh started
