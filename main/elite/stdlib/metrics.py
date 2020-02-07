from __future__ import absolute_import

from traits.api import Bool, Enum, Float
from ..model import Metric
from ..r import ast
from ..r.traits import RExpressionTrait, RNameTrait


class ValueMetric(Metric):

    expression = RExpressionTrait()
    
    def _ast_impl(self):
        return ast.Raw(self.expression)

class EntropyMetric(Metric):

    expression = RExpressionTrait()
    method = Enum('frequent', 'normal')

    def ast(self):
        return ast.Call(ast.Name('def_group_metric'),
                        ast.Constant(self.name),
                        ast.Raw(self.expression),
                        ast.Name('entropy_disc'),
                        (ast.Name('type'), ast.Constant(self.method)),
                        print_hint = 'long')


class RatioMetric(Metric):

    numerator = RExpressionTrait()
    denominator = RExpressionTrait()
    
    # Whether to apply a logarithm transformation to the ratio.
    log_transform = Bool(False)
    
    # Whether to the cap the ratio at certain minimum and maximum values.
    cap_below = Bool(False)
    cap_below_at = Float(0.0)
    cap_below_with = Float(0.0)
    cap_above = Bool(False)
    cap_above_at = Float(1.0)
    cap_above_with = Float(1.0)
    
    # Whether to replace zeros, Infs, and NAs.
    replace_zero = Bool(False)
    replace_zero_with = Float()
    replace_inf = Bool(False)
    replace_inf_with = Float()
    replace_na = Bool(False)
    replace_na_with = Float()
    
    def _ast_impl(self):
        args = [ ast.Raw(self.numerator), ast.Raw(self.denominator)]
        
        if self.cap_below:
            args += [ (ast.Name('min'), ast.Constant(self.cap_below_at)) ]
            if self.cap_below_at != self.cap_below_with:
                args +=  [ (ast.Name('min_to'), 
                            ast.Constant(self.cap_below_with)) ]
        if self.cap_above:
            args += [ (ast.Name('max'), ast.Constant(self.cap_above_at)) ]
            if self.cap_above_at != self.cap_above_with:
                args +=  [ (ast.Name('max_to'), 
                            ast.Constant(self.cap_above_with)) ]
        
        if self.replace_zero:
            args += [ (ast.Name('zero_to'),
                       ast.Constant(self.replace_zero_with)) ]
        if self.replace_inf:
            args += [ (ast.Name('inf_to'),
                       ast.Constant(self.replace_inf_with)) ]
        if self.replace_na:
            args += [ (ast.Name('na_to'),
                       ast.Constant(self.replace_na_with)) ]
                        
        node = ast.Call(ast.Name('ratio'), args)
        if self.log_transform:
            node = ast.Call(ast.Name('safe_log1p'), node)
        return node
    
    def _cap_above_at_changed(self):
        self.cap_above_with = self.cap_above_at
    
    def _cap_below_at_changed(self):
        self.cap_below_with = self.cap_below_at


class DistributionMetric(Metric):
    
    expression = RExpressionTrait()
    
    kind = Enum('chi_square', 'ks', 'custom')
    custom_function = RNameTrait()
    
    def ast(self):
        R_funcs = { 'chi_square': 'chisq_test',
                    'ks' : 'ks.stat',
                    'custom': self.custom_function, }
        return ast.Call(ast.Name('def_group_metric'),
                        ast.Constant(self.name),
                        ast.Raw(self.expression),
                        ast.Name(R_funcs[self.kind]),
                        print_hint = 'long')


class UniqueDiscreteMetric(Metric):

    expression = RExpressionTrait()
    method = Enum('distinct', 'frequent')

    def ast(self):
        return ast.Call(ast.Name('def_group_metric'),
                        ast.Constant(self.name),
                        ast.Raw(self.expression),
                        ast.Name('uniq_disc'),
                        (ast.Name('type'), ast.Constant(self.method)),
                        print_hint = 'long')


class UniqueContinuousMetric(Metric):

    expression = RExpressionTrait()

    def ast(self):
        return ast.Call(ast.Name('def_group_metric'),
                        ast.Constant(self.name),
                        ast.Raw(self.expression),
                        ast.Name('uniq_cont'),
                        print_hint = 'long')


class GraphDensityMetric(Metric):

    expression = RExpressionTrait()

    def ast(self):
        return ast.Call(ast.Name('def_group_metric'),
                        ast.Constant(self.name),
                        ast.Raw(self.expression),
                        ast.Name('graph_density'),
                        print_hint = 'long')