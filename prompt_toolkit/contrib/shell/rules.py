"""
Rules for representing the grammar of a shell command line.

The grammar is defined as a regular langaage, the alphabet consists tokens
delivered by the lexer. Learn more about regular languages on Wikipedia:
http://en.wikipedia.org/wiki/Regular_language

We have the following constructs for defining the language.

 - Literal:
   Defines a Singleton language, matches one token.

 - Sequence:
   Defines a language that is a concatenation of others.

 - Any:
   Union operation.


Example:

::

    # Define the grammar
    grammar = Any([
                    Sequence([ Literal('Hello'), Literal('World') ]),
                    Sequence([ Literal('Something'), Literal('Else') ]),
                ])

    # Create a stream of the input text.
    stream = TokenStream(['Hello', 'World'])

    # Call parser (This yields all the possible parse trees. -- as long as the
    # input document is not complete, there can be several incomplete possible
    # parse trees. -- The grammar can be ambiguous in that case.)
    for tree in grammar.parse(stream):
        print(tree)

"""
from pygments.token import Token

import six
import re

from .nodes import AnyNode, SequenceNode, RepeatNode, LiteralNode, VariableNode, EmptyNode
from prompt_toolkit.code import Completion

__all__ = (
    # Classes for defining the grammar.
    'Any',
    'Literal',
    'Repeat',
    'Sequence',
    'Variable'

    # Wrapper around the input tokens.
    'TokenStream',
)


class Rule(object):
    """
    Abstract base class for any rule.

    A rule represents the grammar of a regular language.
    """
    placeholder_token_class = Token.Placeholder

    def __init__(self, placeholder='', dest=None):
        self.placeholder = placeholder
        self.dest = dest

    @property
    def matches_empty_input(self):
        """
        Boolean indicating that calling parse with an empty input would yield a
        valid parse tree matching the grammar.
        """
        return False

    def parse(self, lexer_stream, allow_incomplete_trees=True):
                                            # TODO: implement option: allow_incomplete_trees=True
                                            # TODO: OR REMOVE THIS OPTION (I don't think we still need it.)
        """
        Yield a list of possible parse trees.

        We avoid yielding too many trees.
        But suppose our grammar is:
        ( "a" "b" "c" ) | ( "a" "b" "c" )
        and our input is:
        "a" "b"
        then we can yield both options.
        There is no obvious way to yield them as a single incomplete parse
        tree, because the parser is in an obviously different state.
        """
        if False:
            yield

    def get_help_tokens(self):
        """
        Generate help text for this rule.
        (Yieds (Token, text) tuples.)
        """
        yield (self.placeholder_token_class, self.placeholder)


class Sequence(Rule):
    """
    Concatenates several other rules.
    """
    def __init__(self, rules, placeholder=None, dest=None):
        assert isinstance(rules, list)

        super(Sequence, self).__init__(placeholder, dest)
        self.rules = rules

    def __repr__(self):
        return 'Sequence(rules=%r)' % self.rules

    @property
    def matches_empty_input(self):
        return all(r.matches_empty_input for r in self.rules)

    def parse(self, lexer_stream):
        def _parse(rules):
            if rules and (rules[0].matches_empty_input or lexer_stream.has_more_tokens):
                for tree in rules[0].parse(lexer_stream):
                    with lexer_stream.restore_point:
                        for suffix in _parse(rules[1:]):
                            yield [ tree ] + suffix
            else:
                yield []

        if lexer_stream.has_more_tokens:
            for lst in _parse(self.rules):
                yield SequenceNode(self, lst)
        else:
            yield EmptyNode(self)

    def get_help_tokens(self):
        first = True
        for c in self.rules:
            if not first:
                yield (Token, ' ')
            first = False

            for k in c.get_help_tokens():
                yield k

    def complete(self, text=''):
        for completion in self.rules[0].complete(text):
            yield completion


class Any(Rule):
    """
    Union of several other rules.

    If the input matches any of the rules, the input matches the defined
    grammar.
    """
    def __init__(self, rules, placeholder=None, dest=None):
        assert len(rules) >= 1

        super(Any, self).__init__(placeholder, dest)
        self.rules = rules

    def __repr__(self):
        return 'Any(rules=%r)' % self.rules

    @property
    def matches_empty_input(self):
        return any(r.matches_empty_input for r in self.rules)

    def parse(self, lexer_stream):
        if lexer_stream.has_more_tokens:
            for rule in self.rules:
                with lexer_stream.restore_point:
                    for result in rule.parse(lexer_stream):
                        yield AnyNode(self, result)
        else:
            yield EmptyNode(self)

    def complete(self, text=''):
        for r in self.rules:
            for c in r.complete(text):
                yield c

    def get_help_tokens(self):
        # The help text is a concatenation of the available options, surrounded
        # by brackets.
        if len(self.rules) > 1:
            yield (Token.Placeholder.Bracket, '[')

        first = True
        for r in self.rules:
            if not first:
                yield (Token.Placeholder.Separator, '|')

            for t in r.get_help_tokens():
                yield t
            first = False

        if len(self.rules) > 1:
            yield (Token.Placeholder.Bracket, ']')


class Repeat(Rule):
    """
    Allow the input to be a repetition of the given grammar.
    (The empty input is a valid match here.)

    The "Kleene star" operation of another rule.
    http://en.wikipedia.org/wiki/Kleene_star
    """
    def __init__(self, rule, placeholder=None, dest=None):
        super(Repeat, self).__init__(placeholder, dest)
        self.rule = rule

        # Don't allow empty rules inside a Repeat clause.
        # (This causes eternal recursion in the parser.)
        # If this happens, there should be a much better way to define the grammar.
        if rule.matches_empty_input:
            raise Exception('Rule %r can not be nested inside Repeat because it matches the empty input.' % rule)

    @property
    def matches_empty_input(self):
        """ (An empty input is always a valid match for a repeat rule.) """
        return True

    def parse(self, lexer_stream):
        def _parse():
            found = False

            if lexer_stream.has_more_tokens:
                for tree in self.rule.parse(lexer_stream):
                    with lexer_stream.restore_point:
                        for suffix in _parse():
                            yield [ tree ] + suffix
                            found = True

            if not found:
                yield []

        if lexer_stream.has_more_tokens:
            for lst in _parse():
                yield RepeatNode(self, lst, lexer_stream.has_more_tokens)
        else:
            yield RepeatNode(self, [], False)

    def complete(self, text=''):
        for c in self.rule.complete(text):
            yield c

    def get_help_tokens(self):
        for t in self.rule.get_help_tokens():
            yield t

        yield (Token.Placeholder, '...')


class Literal(Rule):
    """
    Represents a language consisting of one token, the given string.
    """
    def __init__(self, text, dest=None):
        assert isinstance(text, six.string_types)
        super(Literal, self).__init__(text, dest)

        self.text = text

    def __repr__(self):
        return 'Literal(text=%r)' % self.text

    def parse(self, lexer_stream):
        if lexer_stream.has_more_tokens:
            text = lexer_stream.pop()

            if text == self.text:
                yield LiteralNode(self, text)
        else:
            yield EmptyNode(self)

    def complete(self, text=''):
        if self.text.startswith(text):
            yield Completion(self.text, self.text[len(text):])


class Variable(Rule):
    """
    Represents a language consisting of one token, the given variable.
    """
    placeholder_token_class = Token.Placeholder.Variable

    def __init__(self, completer=None, regex=None, placeholder=None, dest=None):
        super(Variable, self).__init__(placeholder, dest)

        self._completer = completer() if completer else None
        self._regex = re.compile(regex) if regex else None

    def __repr__(self):
        return 'Variable(completer=%r)' % self._completer

    def parse(self, lexer_stream):
        if lexer_stream.has_more_tokens:
            # TODO: only yield if the text matches the regex.
            text = lexer_stream.pop()
            yield VariableNode(self, text)
        else:
            yield EmptyNode(self)

    def complete(self, text=''):
        if self._completer:
            for c in self._completer.complete(text):
                yield c



'''
TODO: implement Optional as follows:

def Optional(rule):
    """ Optional is an 'Any' between the empty sequence or the actual rule. """
    return Any([
        Sequence([]),
        rule
    ])
'''



class TokenStream(object):
    """
    Wraps a stream of the input tokens.
    (Usually, this are the unescaped tokens, received from the lexer.)

    This input stream implements the push/pop stack required for the
    backtracking for parsing the regular grammar.
    """
    def __init__(self, tokens=None):
        self._tokens = (tokens or [])[::-1]

    @property
    def has_more_tokens(self):
        """ True when we have more tokens. """
        return len(self._tokens) > 0

    @property
    def first_token(self):
        if self._tokens:
            return self._tokens[-1]

    def pop(self):
        """ Pop first token from the stack. """
        return self._tokens.pop()

    def __repr__(self):
        return 'TokenStream(tokens=%r)' % self._tokens

    @property
    def restore_point(self):
        """
        Create restore point using a context manager.

        This will save the current state and restore it after the
        context manager is quit.
        """
        class RestoreContext(object):
            def __enter__(c):
                c._tokens = self._tokens[:]

            def __exit__(c, *a):
                self._tokens = c._tokens

        return RestoreContext()
