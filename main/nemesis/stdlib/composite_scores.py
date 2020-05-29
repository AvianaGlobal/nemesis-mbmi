from __future__ import absolute_import

from traits.api import Bool, Float, Instance, Int, List, on_trait_change
from nemesis.model import CompositeScore, Metric
from nemesis.r import ast, ast_macros
from nemesis.r.traits import RExpressionTrait
from nemesis.serialize import DirtyMixin


class CustomScore(CompositeScore):

    expression = RExpressionTrait()
    
    def _ast_impl(self):
        return ast.Raw(self.expression)


class LinearCombinationScore(CompositeScore):
    
    terms = List(Instance('LinearTerm'))
    
    def _ast_impl(self):
        terms = [ ast_macros.Product(ast.Constant(term.coeff), 
                                     ast.Name(term.metric.name))
                  for term in self.terms if term.coeff != 0 ]
        return ast_macros.Sum(terms)
    
    @on_trait_change('terms.dirtied')
    def _set_dirted(self):
        self.dirtied = True

class LinearTerm(DirtyMixin):
    
    coeff = Float()
    metric = Instance(Metric)


class PrincipalComponentScore(CompositeScore):

    top_percent = Float(1.0)
    top_count = Int(1)
    is_percent = Bool(True)

    def _ast_nonstandard_eval(self):
        return False

    def _ast_impl(self):
        top = self.top_percent if self.is_percent else self.top_count

        return [
            ast.Name('composite.pca'),
            (ast.Name('top'), ast.Constant(top)),
            (ast.Name('percent'), ast.Constant(self.is_percent))
        ]

