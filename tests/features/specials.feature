Feature: Special commands

  @wip
  Scenario: run refresh command
     Given we have pgcli installed
      when we run pgcli
      and we wait for prompt
      and we refresh completions
      and we wait for prompt
      then we see completions refresh started
