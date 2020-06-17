from __future__ import absolute_import

from traits.api import BaseStr


class RExpressionTrait(BaseStr):
    """ An R expression.
    """

    def validate(self, object, name, value):
        from .parse import is_expression
        
        value = super(RExpressionTrait, self).validate(object, name, value)
        if len(value) == 0 or is_expression(value):
            return value
        
        self.error(object, name, value)


class RNameTrait(BaseStr):
    """ An (assignable) R name.
    """

    def validate(self, object, name, value):
        from .names import is_name
        
        value = super(RNameTrait, self).validate(object, name, value)
        if len(value) == 0 or is_name(value):
            return value
        
        self.error(object, name, value)