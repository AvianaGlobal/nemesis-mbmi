""" Functions for validating R names.

References:
-----------
http://stackoverflow.com/questions/8396577
http://cran.r-project.org/doc/manuals/r-release/R-lang.html#Reserved-words
"""
from __future__ import absolute_import

import re

keywords = ['if', 'else', 'repeat', 'while', 'function', 'for', 'in', 'next',
            'break', 'TRUE', 'FALSE', 'NULL', 'Inf', 'NaN', 'NA',
            'NA_integer_', 'NA_real_', 'NA_complex_', 'NA_character_']


def is_reserved(s):
    """ Is the string a reserved word in R?
    """
    pattern = r'^\.\.\d+$'
    return s in keywords or s == '...' or bool(re.match(pattern, s))

def is_syntactic_name(s):
    """ Is the string a *syntactically* valid R name?

    Note that such names include the reserved words.
    """
    pattern = r'^([a-zA-Z]|[.][a-zA-Z_.]?)[.\w]*$'
    return bool(re.match(pattern, s))

def is_name(s):
    """ Is the string an assignable R name?
    """
    return is_syntactic_name(s) and not is_reserved(s)