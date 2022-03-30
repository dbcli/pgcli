Releasing pgcli
---------------

You have been made the maintainer of `pgcli`? Congratulations! We have a release script to help you:

```sh
> python release.py --help
Usage: release.py [options]

Options:
  -h, --help           show this help message and exit
  -c, --confirm-steps  Confirm every step. If the step is not confirmed, it
                       will be skipped.
  -d, --dry-run        Print out, but not actually run any steps.
```

The script can be run with `-c` to confirm or skip steps. There's also a `--dry-run` option that only prints out the steps.

To release a new version of the package:

* Create and merge a PR to bump the version in the changelog ([example PR](https://github.com/dbcli/pgcli/pull/1325)).
* Pull `main` and bump the version number inside `pgcli/__init__.py`. Do not check in - the release script will do that.
* Make sure you have the dev requirements installed: `pip install -r requirements-dev.txt -U --upgrade-strategy only-if-needed`.
* Finally, run the release script: `python release.py`.
