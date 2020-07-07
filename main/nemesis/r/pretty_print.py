""" Pretty-printer for the R AST.

For references on the R grammar, see ast.py.

TODO:
 - Special functions: if, while, for, etc
 - Function definition: function(x) x+1
"""
from __future__ import absolute_import

import math
from io import BytesIO as StringIO
from textwrap import TextWrapper

from nemesis.r import ast


# Public API

def write_ast(node, out, indent=0):
    """ Pretty-prints an R AST to a file-like object.
    """
    out.write(indent * ' ')
    _write_ast(node, out, indent)

def print_ast(node, indent=0):
    """ Pretty-prints an R AST as a string.
    """
    io = StringIO()
    write_ast(node, io, indent)
    return io.getvalue()


# Private write functions

def _write_ast(node, out, indent):
    for klass in node.__class__.__mro__:
        writer = writers.get(klass)
        if writer:
            return writer(node, out, indent)
    raise TypeError('Unknown node type %s' % node.__class__.__name__)

def _write_constant(node, out, indent):
    value = node.value
    if isinstance(value, bool):
        out.write('TRUE' if value else 'FALSE')
    elif isinstance(value, float) and math.isinf(value):
        out.write('Inf' if value > 0 else '-Inf')
    elif isinstance(value, float) and math.isnan(value):
        # Follow Pandas in using NaN to represent missing data.
        out.write('NA')
    elif isinstance(value, complex):
        new_node = ast.Call(ast.Name('complex'),
                            (ast.Name('real'), ast.Constant(value.real)),
                            (ast.Name('imaginary'), ast.Constant(value.imag)))
        _write_ast(new_node, out, indent)
    elif isinstance(value, unicode):
        out.write(repr(value.encode('ascii')))
    else:
        out.write(repr(value))

def _write_name(node, out, indent):
    out.write(node.value)
    
def _write_call(node, out, indent):
    # Dispatch on the kind of call being made.
    if _is_call_index(node):
        _write_call_index(node, out, indent)
    elif _is_call_operator(node):
        _write_call_operator(node, out, indent)
    else:
        # If we get here, it's a standard function call.
        _write_call_standard(node, out, indent)

def _write_call_index(node, out, indent):
    if not len(node.args) == 2:
        raise ValueError('Malformed index node %r' % node)
    
    _write_ast(node.args[0], out, indent)
    out.write(node.fn.value)
    _write_ast(node.args[1], out, indent)
    out.write(']' if node.fn.value == '[' else ']]')

def _write_call_operator(node, out, indent):
    # Unary case.
    if len(node.args) == 1:
        _write_ast(node.fn, out, indent)
        _write_ast(node.args[0], out, indent)
    
    # Binary case.
    elif len(node.args) == 2:
        # First argument.
        first = node.args[0]
        parens = (_is_call_operator(first) and
                  _operator_precedence(first) < _operator_precedence(node))
        out.write('(' if parens else '')
        _write_ast(first, out, indent)
        out.write(')' if parens else '')
        
        # Operator.
        out.write('' if _print_hint(node) == 'short' else ' ')
        _write_ast(node.fn, out, indent)
        out.write('' if _print_hint(node) == 'short' else ' ')
        
        # Second argument. The difference in inequality strictness is due to
        # R's left-to-right evaluation order for operators of equal precedence.
        second = node.args[1]
        parens = (_is_call_operator(second) and
                  _operator_precedence(second) <= _operator_precedence(node))
        out.write('(' if parens else '')
        _write_ast(second, out, indent)
        out.write(')' if parens else '')
    

def _write_call_standard(node, out, indent):
    _write_ast(node.fn, out, indent)
    out.write('(')

    # We can't predict the length of a general expression.
    if isinstance(node.fn, ast.Name):
        indent += len(node.fn.value) + 1
    else:
        indent += 2

    for i, node_or_pair in enumerate(node.args):
        # Print the argument separator (if not on the first argument).
        if i > 0:
            if _print_hint(node) == 'long':
                out.write(',')
                _write_newline(out, indent)
            else:
                out.write(',' if _print_hint(node) == 'short' else ', ')
        
        # Print the argument itself.
        if isinstance(node_or_pair, tuple):
            _write_ast(node_or_pair[0], out, indent)
            out.write('=' if _print_hint(node) == 'short' else ' = ')
            _write_ast(node_or_pair[1], out, indent)
        else:
            _write_ast(node_or_pair, out, indent)

    out.write(')')

def _write_pair_list(node, out, indent):
    for i, name_or_pair in enumerate(node.value):
         if i > 0:
             out.write(', ')
         if isinstance(name_or_pair, tuple):
             _write_ast(name_or_pair[0], out, indent)
             out.write(' = ')
             _write_ast(name_or_pair[1], out, indent)
         else:
             _write_ast(name_or_pair, out, indent)

def _write_block(node, out, indent):
    for i, expr in enumerate(node.value):
        if i > 0:
            if _print_hint(node) == 'short':
                out.write('; ')
            elif _print_hint(node) == 'long':
                _write_newline(out, 0)
                _write_newline(out, indent)
            else:
                _write_newline(out, indent)
        _write_ast(expr, out, indent)

def _write_comment(node, out, indent):
    wrapper = TextWrapper(initial_indent = '# ',
                          subsequent_indent = indent * ' ' + '# ',
                          break_long_words = False)
    out.write(wrapper.fill(node.value))

def _write_raw(node, out, indent):
    out.write(node.value)

def _write_newline(out, indent):
    out.write('\n')
    out.write(' ' * indent)


# Additional private functions

def _is_call_index(node):
    return (isinstance(node, ast.Call) and 
            isinstance(node.fn, ast.Name) and node.fn.value in ('[', '[['))

def _is_call_operator(node):
    if not (isinstance(node, ast.Call) and isinstance(node.fn, ast.Name)):
        return False
    sym = node.fn.value
    num_args = len(node.args)
    return ((sym, num_args) in OP_PRECEDENCE or
            (sym.startswith('%') and sym.endswith('%') and num_args == 2))

def _operator_precedence(node):
    assert _is_call_operator(node)
    default = OP_PRECEDENCE[('%%', 2)]
    return OP_PRECEDENCE.get((node.fn.value, len(node.args)), default)                 

def _print_hint(node):
    return node.metadata.get('print_hint', 'normal')


# Globals and constants

writers = { ast.Constant: _write_constant,
            ast.Name: _write_name,
            ast.Call: _write_call,
            ast.PairList: _write_pair_list,
            ast.Block: _write_block,
            ast.Comment: _write_comment,
            ast.Raw: _write_raw }

# Binary and unary operators with precedence
# 
# Reference: 
# http://stat.ethz.ch/R-manual/R-patched/library/base/html/Syntax.html
OP_PRECEDENCE = {
    ('^', 2) : 14,
    ('-', 1) : 13, ('+', 1) : 13,
    (':', 2) : 12,
    ('%%', 2) : 11, # Any special operator (including %% and %/%)
    ('*', 2) : 10, ('/', 2) : 10,
    ('+', 2) : 9, ('-', 2) : 9,
    ('<', 2) : 8, ('>', 2) : 8, ('<=', 2) : 8, ('>=', 2) : 8,
    ('==', 2) : 8, ('!=', 2) : 8,
    ('!', 1) : 7,
    ('&', 2) : 6, ('&&', 2) : 6,
    ('|', 2) : 5, ('||', 2) : 5,
    ('~', 2) : 4,
    ('->', 2) : 3, ('->>', 2) : 3,
    ('<-', 2) : 2, ('<<-', 2) : 2,
    ('=', 2) : 1,
    ('?', 1) : 0, ('?', 2) : 0,
}