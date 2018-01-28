from __future__ import unicode_literals
from .application import Application
from prompt_toolkit.input import DummyInput
from prompt_toolkit.output import DummyOutput

__all__ = [
    'DummyApplication',
]


class DummyApplication(Application):
    """
    When no `Application` is running,
    `prompt_toolkit.application.current.get_app` will run an instance of this
    `Application`.
    """
    def __init__(self):
        super(DummyApplication, self).__init__(output=DummyOutput(), input=DummyInput())

    def run(self):
        raise NotImplementedError('A DummyApplication is not supposed to run.')

    def run_async(self):
        raise NotImplementedError('A DummyApplication is not supposed to run.')

    def run_system_command(self):
        raise NotImplementedError

    def suspend_to_background(self):
        raise NotImplementedError
