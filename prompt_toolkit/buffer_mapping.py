from __future__ import unicode_literals
from .enums import DEFAULT_BUFFER, SEARCH_BUFFER, SYSTEM_BUFFER, DUMMY_BUFFER
from .buffer import Buffer, AcceptAction
from .history import InMemoryHistory

__all__ = (
    'BufferMapping',
)


class BufferMapping(dict):
    """
    Dictionary that maps the name of the buffers to the
    :class:`~prompt_toolkit.buffer.Buffer` instances.
    """
    def __init__(self, buffers=None):
        assert buffers is None or isinstance(buffers, dict)

        # Start with an empty dict.
        super(BufferMapping, self).__init__()

        # Add default buffers.
        self.update({
            # For the 'search' and 'system' buffers, 'returnable' is False, in
            # order to block normal Enter/ControlC behaviour.
            DEFAULT_BUFFER: Buffer(accept_action=AcceptAction.RETURN_DOCUMENT),
            SEARCH_BUFFER: Buffer(history=InMemoryHistory(), accept_action=AcceptAction.IGNORE),
            SYSTEM_BUFFER: Buffer(history=InMemoryHistory(), accept_action=AcceptAction.IGNORE),
            DUMMY_BUFFER: Buffer(read_only=True),
        })

        # Add received buffers.
        if buffers is not None:
            self.update(buffers)
