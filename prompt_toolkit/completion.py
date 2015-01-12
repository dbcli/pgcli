"""
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'Completion',
    'Completer',
    'get_common_complete_suffix',
)


class Completion(object):
    def __init__(self, text, start_position=0, display=None, display_meta=''):
        """
        :param text: The new string that will be inserted into the document.
        :param start_position: Position relative to the cursor_position where the
            new text will start. The text will be inserted between the
            start_position and the original cursor position.
        :param display: (optional string) If the completion has to be displayed
            differently in the completion menu.
        :param display_meta: (Optional string) Meta information about the
            completion, e.g. the path or source where it's coming from.
        """
        self.text = text
        self.start_position = start_position
        self.display_meta = display_meta

        if display is None:
            self.display = text
        else:
            self.display = display

        assert self.start_position <= 0

    def __repr__(self):
        return 'Completion(text=%r, start_position=%r)' % (self.text, self.start_position)

    def __eq__(self, other):
        return (
            self.text == other.text and
            self.start_position == other.start_position and
            self.display == other.display and
            self.display_meta == other.display_meta)

    def __hash__(self):
        return hash((self.text, self.start_position, self.display, self.display_meta))


class CompleteEvent(object):
    """
    Event that called the completer.
    """
    def __init__(self, text_inserted=False, completion_requested=False):
        assert not (text_inserted and completion_requested)

        #: Automatic completion while typing.
        self.text_inserted = text_inserted

        #: Used explicitely requested completion by pressing 'tab'.
        self.completion_requested = completion_requested


class Completer(with_metaclass(ABCMeta, object)):
    """
    Base class for Code implementations.

    The methods in here are methods that are expected to exist for the `Buffer`
    and `Renderer` classes.
    """
    @abstractmethod
    def get_completions(self, document, complete_event):
        """
        Yield `Completion` instances.
        """
        while False:
            yield


def get_common_complete_suffix(completer, document, complete_event):
    """
    return one `Completion` instance or None.
    """
    # If there is one completion, return that.
    completions = list(completer.get_completions(document, complete_event))

    # Take only completions that don't change the text before the cursor.
    def doesnt_change_before_cursor(completion):
        end = completion.text[:-completion.start_position]
        return document.text_before_cursor.endswith(end)

    completions = [c for c in completions if doesnt_change_before_cursor(c)]

    # Return the common prefix.
    def get_suffix(completion):
        return completion.text[-completion.start_position:]

    return _commonprefix([get_suffix(c) for c in completions])


def _commonprefix(strings):
    # Similar to os.path.commonprefix
    if not strings:
        return ''

    else:
        s1 = min(strings)
        s2 = max(strings)

        for i, c in enumerate(s1):
            if c != s2[i]:
                return s1[:i]

        return s1
