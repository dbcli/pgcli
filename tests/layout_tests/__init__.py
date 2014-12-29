from __future__ import unicode_literals

#from prompt_toolkit.layout.utils import fit_tokens_in_size
from pygments.token import Token

import unittest


#class FitTokensInSizeTest(unittest.TestCase):
#    def setUp(self):
#        self.tokens = [(Token, 'Hello world'), (Token, '\n'), (Token, 'line2')]
#
#    def test_1(self):
#        result = fit_tokens_in_size(self.tokens, width=5, height=3, default_token=Token)
#
#        self.assertEqual(result, [
#            [(Token, u'H'), (Token, u'e'), (Token, u'l'), (Token, u'l'), (Token, u'o')],
#            [(Token, u'l'), (Token, u'i'), (Token, u'n'), (Token, u'e'), (Token, u'2')],
#            [(Token, u'     ')],
#        ])
#
#    def test_2(self):
#        result = fit_tokens_in_size(self.tokens, width=3, height=3, default_token=Token)
#
#        self.assertEqual(result, [
#            [(Token, u'H'), (Token, u'e'), (Token, u'l')],
#            [(Token, u'l'), (Token, u'i'), (Token, u'n')],
#            [(Token, u'   ')],
#        ])
#
#    def test_3(self):
#        result = fit_tokens_in_size(self.tokens, width=3, height=2, default_token=Token)
#
#        self.assertEqual(result, [
#            [(Token, u'H'), (Token, u'e'), (Token, u'l')],
#            [(Token, u'l'), (Token, u'i'), (Token, u'n')],
#        ])
#
#    def test_4(self):
#        result = fit_tokens_in_size(self.tokens, width=3, height=1, default_token=Token)
#
#        self.assertEqual(result, [
#            [(Token, u'H'), (Token, u'e'), (Token, u'l')],
#        ])
#
#    def test_5(self):
#        result = fit_tokens_in_size(self.tokens, width=15, height=4, default_token=Token)
#
#        self.assertEqual(result, [
#            [(Token, u'H'), (Token, u'e'), (Token, u'l'), (Token, u'l'), (Token, u'o'), (Token, u' '),
#                (Token, u'w'), (Token, u'o'), (Token, u'r'), (Token, u'l'), (Token, u'd'), (Token, u'    ')],
#            [(Token, u'l'), (Token, u'i'), (Token, u'n'), (Token, u'e'), (Token, u'2'), (Token, u'          ')],
#            [(Token, u' ' * 15)],
#            [(Token, u' ' * 15)],
#        ])
