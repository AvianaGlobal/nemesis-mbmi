""" Functions for manipulating R ASTs.
"""
from __future__ import absolute_import

from collections import deque

from . import ast


def find_libraries(node):
    """ Aggregate all the library metadata associated with the AST.
    
    Looks for the 'libraries' key, whose value should be a list of strings.
    """
    libraries = []
    for child in traverse_ast(node):
        libraries.extend(child.metadata.get('libraries', []))
    return libraries


def traverse_ast(node, depth_first=False):
    """ Yields every node in the AST.
    
    By default, the search is breadth-first.
    """
    stack = deque([node])
    if depth_first:
        stack_pop = stack.pop
        stack_extend = stack.extend
    else:
        stack_pop = stack.popleft
        stack_extend = stack.extend
    
    while stack:
        node = stack_pop()
        yield node
    
        if isinstance(node, ast.Block):
            stack_extend(node.value)
        
        elif isinstance(node, ast.Call):
            children = [node.fn]
            for node_or_pair in node.args:
                if isinstance(node_or_pair, ast.Node):
                    children.append(node_or_pair)
                else:
                    children.extend(node_or_pair)
            stack_extend(children)