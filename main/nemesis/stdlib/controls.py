from __future__ import absolute_import
from traits.api import Bool, Either, Float, Int, List, Range, Str
from nemesis.model import Control, ModelError
from nemesis.r import ast, ast_macros
from nemesis.r.traits import RExpressionTrait


class FactorControl(Control):
    expression = RExpressionTrait()
    
    def _ast_impl(self):
        return ast.Raw(self.expression)


class NumericalControl(Control):
    expression = RExpressionTrait()
    auto_breaks = Bool(True)
    num_breaks = Range(low=2, value=10)
    breaks = List(Either(Int, Float))
    closed_on_left = Bool(True)
    labels = List(Str)

    def _ast_impl(self):
        args = [ ast.Raw(self.expression) ]
        if self.auto_breaks:
            arg_breaks = ast.Constant(self.num_breaks)
        else:
            arg_breaks = ast_macros.seq_to_vector(self.breaks)
        args.append((ast.Name('breaks'), arg_breaks))
        if self.labels:
            args.append((ast.Name('labels'),
                         ast_macros.seq_to_vector(self.labels)))
        if self.closed_on_left:
            # By default, R closes on the right.
            args.append((ast.Name('right'), ast.Constant(False)))
        return ast.Call(ast.Name('cut'), args, print_hint='long')
    
    def validate(self):
        num_breaks = self.num_breaks if self.auto_breaks else len(self.breaks)
        if self.labels and len(self.labels) != num_breaks - 1:
            msg = "Numerical control variable: incorrect number of labels"
            raise ModelError(msg)
