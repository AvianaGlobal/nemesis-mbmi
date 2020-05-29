from __future__ import absolute_import

from enaml.validator import Validator

from nemsis.r.parse import is_expression


class RExpressionValidator(Validator):
    """ A validator that handles R expressions.
    """
    
    def validate(self, text):
        """ Validates the text as the user types.
        """
        return is_expression(text)


class RFloatValidator(Validator):
    """ A validator that handles R floating point numbers (reals).
    """
    
    def validate(self, text):
        """ Validates the text as the user types.
        """
        from ..float import r_float
        try:
            r_float(text)
        except ValueError:
            return False
        else:
            return True


class RNameValidator(Validator):
    """ A validator that handles R names.
    """
    
    def validate(self, text):
        """ Validates the text as the user types.
        """
        from ..names import is_name
        return is_name(text)