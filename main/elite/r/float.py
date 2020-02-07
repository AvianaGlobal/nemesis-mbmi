from __future__ import absolute_import

from . import ast
from .pretty_print import print_ast


def r_float(text):
    """ Convert a float string in R syntax to a Python float.
    
    Raises a ValueError if this is not possible.
    """
    r_to_python = {
        'Inf': 'inf', '-Inf': '-inf', 'NA': 'nan', 'NaN': 'nan',
    }
    text = text.strip()
    if text in r_to_python:
        text = r_to_python[text]
    return float(text)


def r_format_number(value):
    """ Format a Python number as an R constant.
    """
    return print_ast(ast.Constant(value))