from .rpy2 import rinterface as ri


def is_expression(text):
    """ Determine whether `text` is a single, valid R expression.
    """
    try:
        expression = ri.parse(text)
    except (ValueError, ri.RParsingIncompleteError, ri.RParsingError):
        return False

    if len(expression) != 1:
        return False

    expression = expression[0]

    expr_type = ri.str_typeint(expression.typeof)
    return expr_type in (
        'LANGSXP', 'SYMSXP', 'CPLXSXP', 'LGLSXP', 'REALSXP', 'STRSXP'
    )

ri.initr()

METHOD_TABLE = {
    'is_expression': is_expression,
}
