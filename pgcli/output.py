import click

# output interface:
#   def emit(self, cmd: str, output: str) -> None


class Pager:
    """
    An output target which emits to the pager via the PGCli object.
    """

    def __init__(self, cli):
        self._cli = cli

    def emit(self, cmd, output):
        self._cli.echo_via_pager(output)


class Stdout:
    """
    An output which emits to stdout via `click.echo()`.
    """

    def emit(self, cmd, output):
        click.echo(output)


class Log:
    """
    An output wrapper which optionally emits to a log file instead.
    """

    def __init__(self, cli, parent):
        self._cli = cli
        self._parent = parent

    def _emit(self, cmd, output):
        if self._cli.output_file and not cmd.startswith(("\\o ", "\\? ")):
            try:
                with open(self._cli.output_file, "a", encoding="utf-8") as f:
                    click.echo(cmd, file=f)
                    click.echo(output, file=f)
                    click.echo("", file=f)  # extra newline
            except OSError as e:
                click.secho(str(e), err=True, fg="red")
        elif output:
            self._parent.emit(cmd, output)

    def emit(self, cmd, output):
        try:
            self._emit(cmd, output)
        except KeyboardInterrupt:
            pass
