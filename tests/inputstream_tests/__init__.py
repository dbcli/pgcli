from __future__ import unicode_literals

from prompt_toolkit.terminal.vt100_input import InputStream
from prompt_toolkit.keys import Keys

import unittest


class InputStreamTest(unittest.TestCase):
    def setUp(self):
        class _ProcessorMock(object):
            def __init__(self):
                self.keys = []

            def feed_key(self, key_press):
                self.keys.append(key_press)

        self.processor = _ProcessorMock()
        self.stream = InputStream(self.processor.feed_key)

    def test_control_keys(self):
        self.stream.feed('\x01\x02\x10')

        self.assertEqual(len(self.processor.keys), 3)
        self.assertEqual(self.processor.keys[0].key, Keys.ControlA)
        self.assertEqual(self.processor.keys[1].key, Keys.ControlB)
        self.assertEqual(self.processor.keys[2].key, Keys.ControlP)
        self.assertEqual(self.processor.keys[0].data, '\x01')
        self.assertEqual(self.processor.keys[1].data, '\x02')
        self.assertEqual(self.processor.keys[2].data, '\x10')

    def test_arrows(self):
        self.stream.feed('\x1b[A\x1b[B\x1b[C\x1b[D')

        self.assertEqual(len(self.processor.keys), 4)
        self.assertEqual(self.processor.keys[0].key, Keys.Up)
        self.assertEqual(self.processor.keys[1].key, Keys.Down)
        self.assertEqual(self.processor.keys[2].key, Keys.Right)
        self.assertEqual(self.processor.keys[3].key, Keys.Left)
        self.assertEqual(self.processor.keys[0].data, '\x1b[A')
        self.assertEqual(self.processor.keys[1].data, '\x1b[B')
        self.assertEqual(self.processor.keys[2].data, '\x1b[C')
        self.assertEqual(self.processor.keys[3].data, '\x1b[D')

    def test_escape(self):
        self.stream.feed('\x1bhello')

        self.assertEqual(len(self.processor.keys), 1 + len('hello'))
        self.assertEqual(self.processor.keys[0].key, Keys.Escape)
        self.assertEqual(self.processor.keys[1].key, 'h')
        self.assertEqual(self.processor.keys[0].data, '\x1b')
        self.assertEqual(self.processor.keys[1].data, 'h')

    def test_special_double_keys(self):
        self.stream.feed('\x1b[1;3D')  # Should both send escape and left.

        self.assertEqual(len(self.processor.keys), 2)
        self.assertEqual(self.processor.keys[0].key, Keys.Escape)
        self.assertEqual(self.processor.keys[1].key, Keys.Left)
        self.assertEqual(self.processor.keys[0].data, '\x1b[1;3D')
        self.assertEqual(self.processor.keys[1].data, '\x1b[1;3D')

    def test_flush_1(self):
        # Send left key in two parts without flush.
        self.stream.feed('\x1b')
        self.stream.feed('[D')

        self.assertEqual(len(self.processor.keys), 1)
        self.assertEqual(self.processor.keys[0].key, Keys.Left)
        self.assertEqual(self.processor.keys[0].data, '\x1b[D')

    def test_flush_2(self):
        # Send left key with a 'Flush' in between.
        # The flush should make sure that we process evenything before as-is,
        # with makes the first part just an escape character instead.
        self.stream.feed('\x1b')
        self.stream.flush()
        self.stream.feed('[D')

        self.assertEqual(len(self.processor.keys), 3)
        self.assertEqual(self.processor.keys[0].key, Keys.Escape)
        self.assertEqual(self.processor.keys[1].key, '[')
        self.assertEqual(self.processor.keys[2].key, 'D')

        self.assertEqual(self.processor.keys[0].data, '\x1b')
        self.assertEqual(self.processor.keys[1].data, '[')
        self.assertEqual(self.processor.keys[2].data, 'D')

    def test_meta_arrows(self):
        self.stream.feed('\x1b\x1b[D')

        self.assertEqual(len(self.processor.keys), 2)
        self.assertEqual(self.processor.keys[0].key, Keys.Escape)
        self.assertEqual(self.processor.keys[1].key, Keys.Left)

    def test_control_square_close(self):
        self.stream.feed('\x1dC')

        self.assertEqual(len(self.processor.keys), 2)
        self.assertEqual(self.processor.keys[0].key, Keys.ControlSquareClose)
        self.assertEqual(self.processor.keys[1].key, 'C')

    def test_invalid(self):
        # Invalid sequence that has at two characters in common with other
        # sequences.
        self.stream.feed('\x1b[*')

        self.assertEqual(len(self.processor.keys), 3)
        self.assertEqual(self.processor.keys[0].key, Keys.Escape)
        self.assertEqual(self.processor.keys[1].key, '[')
        self.assertEqual(self.processor.keys[2].key, '*')

    def test_cpr_response(self):
        self.stream.feed('a\x1b[40;10Rb')
        self.assertEqual(len(self.processor.keys), 3)
        self.assertEqual(self.processor.keys[0].key, 'a')
        self.assertEqual(self.processor.keys[1].key, Keys.CPRResponse)
        self.assertEqual(self.processor.keys[2].key, 'b')

    def test_cpr_response_2(self):
        # Make sure that the newline is not included in the CPR response.
        self.stream.feed('\x1b[40;1R\n')
        self.assertEqual(len(self.processor.keys), 2)
        self.assertEqual(self.processor.keys[0].key, Keys.CPRResponse)
        self.assertEqual(self.processor.keys[1].key, Keys.ControlJ)
