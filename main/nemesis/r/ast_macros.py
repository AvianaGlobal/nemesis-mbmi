""" Convenience macros for building R ASTs.
"""
from __future__ import absolute_import

from .ast import Constant, Name, Call, star_args_to_list


def Assign(name, value):
    """ Macro to create assignment call.
    """
    return Call(Name('<-'), name, value)

def Sum(*args):
    """ Macro to add an arbitrary number of arguments.
    """
    args = star_args_to_list(args)
    return OperatorReduce(Name('+'), args, Constant(0))

def Product(*args):
    """ Macro to multiply an arbitrary number of arguments.
    """
    args = star_args_to_list(args)
    return OperatorReduce(Name('*'), args, Constant(1))

def OperatorReduce(op, args, default=None):
    """ Reduces the argument list by applying a binary operator.
    
    Assumes the operator is left associative.
    """
    if len(args) == 0:
        if default is None:
            raise ValueError('Empty list and no default value')
        else:
            return default
    elif len(args) == 1:
        return args[0]
    else:
        return Call(op, OperatorReduce(op, args[:-1], default), args[-1])


def cast_to_constant(val):
    """ Ensure that the value is a Constant.
    """
    if not isinstance(val, Constant):
        val = Constant(val)
    return val


def seq_to_list(seq):
    """ Convert a Python sequence to an R list.
    """
    return Call(Name('list'), [ cast_to_constant(item) for item in seq ])

def seq_to_vector(seq):
    """ Convert a Python sequence to an R vector.
    """
    # R does not distinguish between length 1 vectors and scalars.
    if len(seq) == 1:
        return cast_to_constant(seq[0])
    
    return Call(Name('c'), [ cast_to_constant(item) for item in seq ])
