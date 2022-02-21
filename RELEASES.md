Releasing pgcli
---------------

We have a script called `release.py` to automate the process.

The script can be run with `-c` to confirm or skip steps. There's also a `--dry-run` option that only prints out the steps.

```
> python release.py --help
Usage: release.py [options]

Options:
  -h, --help           show this help message and exit
  -c, --confirm-steps  Confirm every step. If the step is not confirmed, it
                       will be skipped.
  -d, --dry-run        Print out, but not actually run any steps.
```
