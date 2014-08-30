"""
Nodes for representing the parse tree.

The return type for `.rule.Rule.parse`.
"""
from pygments.token import Token

__all__ = ('AnyNode', 'LiteralNode', 'RepeatNode', 'SequenceNode',  'VariableNode')


class ParseNode(object):
    def __init__(self, rule):
        self.rule = rule

    @property
    def is_complete(self):
        """
        Boolean, indicating that we have a gramatical match; all the
        variables/literals are filled in.
        """
        return True

    @property
    def is_extendible(self):
        """
        Boolean, indicating whether this node could consume any more tokens.
        In case of repeats for instance, a node can keep consuming tokens.
        """
        return not self.is_complete

    def complete(self, text=''):
        """
        Given the beginning text of the *following* token, yield a list of
        `Completion` instances.
        """
        if False:
            yield

    def get_help_tokens(self):
        """
        Only yield a help part if this node didn't contain any text yet.
        """
        if not self._text:
            for t in self.rule.get_help_tokens():
                yield t

    def get_variables(self):
        """
        Get a dictionary that contains all the variables (`dest` in the grammar
        tree definition.).
        """
        if self.rule.dest:
            return { self.rule.dest: True }
        else:
            return { }


class EmptyNode(ParseNode):
    """
    When the inputstream is empty, but input tokens are required, this node is
    a placeholder for expected input.
    """
    def __repr__(self):
        return 'EmptyNode(%r)' % self.rule

    # This node is obviously not complete, as we lack an input token.
    is_complete = False

    def complete(self, text=''):
        for c in self.rule.complete(text):
            yield c

    def get_help_tokens(self):
        for k in self.rule.get_help_tokens():
            yield k


class SequenceNode(ParseNode):
    """ Parse tree result of sequence """
    def __init__(self, rule, children):
        super(SequenceNode, self).__init__(rule)
        self.children = children

    def __repr__(self):
        return 'SequenceNode(%r)' % self.children

    @property
    def is_complete(self):
        return len(self.children) == len(self.rule.rules) and all(d.is_complete for d in self.children)

    @property
    def is_extendible(self):
        """ This node can be extended as long as it's incomplete, or the last
        child is extendible (repeatable). """
        return not self.is_complete or (self.children and self.children[-1].is_extendible)

    def complete(self, text=''):
        # When the last child node is unfinished, complete that.
        # (e.g. nested Sequence, only containing a few tokens.)
        if self.children and not self.children[-1].is_complete:
            for completion in self.children[-1].complete(text):
                yield completion

        # Every child in this sequence is 'complete.'
        else:
            # Complete using the first following rule.
            if len(self.children) < len(self.rule.rules):
                for completion in self.rule.rules[len(self.children)].complete(text):
                    yield completion

            # If the last child allows repetitions (Nested repeat.)
            if self.children and self.children[-1].is_extendible:
                for completion in self.children[-1].complete(text):
                    yield completion

    def get_help_tokens(self):
        first = True
        if self.children and self.children[-1].is_extendible:
            for k in self.children[-1].get_help_tokens():
                yield k
            first = False

        for rule in self.rule.rules[len(self.children):]:
            if not first:
                yield (Token, ' ')
            first = False

            for k in rule.get_help_tokens():
                yield k

    def get_variables(self):
        result = super(SequenceNode, self).get_variables()
        for c in self.children:
            result.update(c.get_variables())
        return result


class RepeatNode(ParseNode):
    def __init__(self, rule, children, tokens_after):
        super(RepeatNode, self).__init__(rule)
        self.children = children

        #: True if there were input tokens following this tree.
        self._tokens_after = tokens_after

    def __repr__(self):
        return 'RepeatNode(%r)' % self.children

    @property
    def is_complete(self): # TODO: revise the definition of 'is_complete'... (does it mean not showing help info or processable?)
        # Note that an empty repeat is also 'complete'
        return all(c.is_complete for c in self.children)

    @property
    def is_extendible(self):
        return True

    def complete(self, text=''):
        if self.children and not self.children[-1].is_complete:
            for c in self.children[-1].complete(text):
                yield c
        else:
            for c in self.rule.complete(text):
                yield c

    def get_help_tokens(self):
        # If in the original input, there were tokens following the repeat, then
        # we can consider this node complete.
        if self._tokens_after:
            pass

        # If we don't have children yet, take the help of the nested grammar itself.
        elif not self.children or self.is_complete:
            for t in self.rule.get_help_tokens():
                yield t

        else:
            for k in self.children[-1].get_help_tokens():
                yield k

    def get_variables(self):
        result = super(RepeatNode, self).get_variables()
        for c in self.children:
            result.update(c.get_variables())
        return result


class AnyNode(ParseNode):
    def __init__(self, rule, child):
        assert isinstance(child, ParseNode)

        super(AnyNode, self).__init__(rule)
        self.child = child

    def __repr__(self):
        return 'AnyNode(%r)' % self.child

    @property
    def is_complete(self):
        return self.child.is_complete

    @property
    def is_extendible(self):
        return self.child.is_extendible

    def complete(self, text=''):
        for completion in self.child.complete(text):
            yield completion

    def get_help_tokens(self):
        for t in self.child.get_help_tokens():
            yield t

    def get_variables(self):
        result = super(AnyNode, self).get_variables()
        result.update(self.child.get_variables())
        return result


class LiteralNode(ParseNode):
    def __init__(self, rule, text):
        #assert isinstance(rule, Literal)
        super(LiteralNode, self).__init__(rule)
        self._text = text

    def __repr__(self):
        return 'LiteralNode(%r)' % self._text

    def get_variables(self):
        if self.rule.dest:
            return { self.rule.dest: self._text }
        else:
            return { }


class VariableNode(ParseNode):
    def __init__(self, rule, text):
        #assert isinstance(rule, Variable)
        super(VariableNode, self).__init__(rule)
        self._text = text

    def __repr__(self):
        return 'VariableNode(%r)' % self._text

    def get_variables(self):
        if self.rule.dest:
            return { self.rule.dest: self._text }
        else:
            return { }
