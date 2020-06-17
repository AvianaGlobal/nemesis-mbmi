""" An AST (abstract syntax tree) for R.

References:
-----------
http://adv-r.had.co.nz/Expressions.html
https://github.com/antlr/grammars-v4/blob/master/r/R.g4
"""
from __future__ import absolute_import

from traits.api import HasStrictTraits, Any, Bool, Int, Float, Complex, Str, \
    Dict, Either, Instance, List, Tuple, Unicode


# Base node classes

class Node(HasStrictTraits):
    # Metadata associated with the node. This data has no semantic value in the
    # AST but may used by external applications for any purpose.
    #
    # For example, the pretty printer looks for 'print_hint' for hints about
    # how to print the node (possible values are 'short', 'normal', long').
    metadata = Dict(Str, Any)


class ValueNode(Node):
    value = Any()

    def __init__(self, value, **metadata):
        super(ValueNode, self).__init__(value=value, metadata=metadata)

    def __eq__(self, other):
        return (type(self) is type(other) and self.value == other.value)

    def __repr__(self):
        return '{name}({value})'.format(name=self.__class__.__name__,
                                        value=repr(self.value))


# The four kinds of R expressions

class Constant(ValueNode):
    value = Either(Bool, Int, Float, Complex, Str)


class Name(ValueNode):
    # Any symbol (including operators like '+'), not just valid R names
    # (in R, such symbols can be obtained using backticks, e.g., `+`).
    value = Str()


class Call(Node):
    fn = Instance(Node)
    args = List(Either(Node, Tuple(Name, Node)))

    def __init__(self, fn, *args, **metadata):
        args = star_args_to_list(args)
        super(Call, self).__init__(fn=fn, args=args, metadata=metadata)

    def __eq__(self, other):
        return (isinstance(other, Call) and
                self.fn == other.fn and self.args == other.args)

    def __repr__(self):
        return 'Call({fn}, {args})'.format(fn=repr(self.fn),
                                           args=repr(self.args))


class PairList(ValueNode):
    value = List(Either(Name, Tuple(Name, Node)))


# Other R nodes

class Block(ValueNode):
    """ A sequence of expressions.

    In R, these are set off by braces ('{' and '}').
    """
    value = List(Node)


class Comment(ValueNode):
    value = Unicode()


# Special purpose nodes (not part of R's grammar)

class Raw(ValueNode):
    """ A fake AST node that represents a piece of unparsed (raw) code.
    """
    value = Str()


# Utility functions

def star_args_to_list(args):
    if len(args) == 1 and isinstance(args[0], list):
        args = args[0]
    else:
        args = list(args)
    return args
