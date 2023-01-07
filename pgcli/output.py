import click

# output interface:
#   def emit(self, cmd: str, output: str) -> None


class OutputHandler:
    """
    An output which ignores the cmd and sends output through a provided handler function.
    """

    def __init__(self, handler):
        self._handler = handler

    def emit(self, _, output):
        self._handler(output)


class Log:
    """
    An output wrapper which optionally emits to a log file instead.
    """

    def __init__(self, logpath, parent):
        self._logpath = logpath
        self.parent = parent

    def update(self, logpath):
        self._logpath = logpath

    def _emit(self, cmd, output):
        if self._logpath and not cmd.startswith(("\\o ", "\\? ")):
            try:
                with open(self._logpath, "a", encoding="utf-8") as f:
                    click.echo(cmd, file=f)
                    click.echo(output, file=f)
                    click.echo("", file=f)  # extra newline
            except OSError as e:
                click.secho(str(e), err=True, fg="red")
        elif output:
            self.parent.emit(cmd, output)

    def emit(self, cmd, output):
        try:
            self._emit(cmd, output)
        except KeyboardInterrupt:
            pass
