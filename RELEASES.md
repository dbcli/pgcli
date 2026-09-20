Releasing pgcli
---------------

You have been made the maintainer of `pgcli`? Congratulations!

To release a new version of the package:

1. Set the version number (that should follow SemVer) in
   `changelog.rst` by turning the "Upcoming" section title into
   something like "4.7.0 (2026-09-19)" (i.e. the version number
   followed by the date of the release, most probably today); and add
   a new empty "Upcoming" section.

2. Set the same version number in `__init__.py`.

3. [Create a new GitHub release](https://github.com/dbcli/pgcli/releases/new):

   1. Click on "Select tag", input the new tag name (it should start
      with "v", for example "v4.7.0") and click "Create new tag".

   2. Select target branch: `main`.

   3. Input release title: the version number (without "v"), for example
      "4.7.0".

   4. In the release notes, copy the corresponding section from
      `changelog.rst`. Double-check the rendered text. Warning:
      changelog is in reSTructuredText, release notes are in Markdown,
      syntax is similar but not exactly compatible.

   5. No binary file to upload, default release label ("Latest"), no
      "discussion for this release".

   6. Click on "Publish release".

   This will trigger a GitHub action that runs all the tests, builds
   the package and uploads it to PyPI.