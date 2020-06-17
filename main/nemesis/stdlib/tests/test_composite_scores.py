from __future__ import absolute_import

import unittest
from ...r.ast import Constant, Name, Call, Raw
from ..metrics import ValueMetric
from ..composite_scores import CustomScore, LinearCombinationScore, LinearTerm


class TestCompositeScores(unittest.TestCase):

    def test_custom_score(self):
        score = CustomScore(name = 'foobar',
                            expression = '0.5*foo + 0.5*bar')
        ast = Call(Name('def_composite_score'),
                   (Name('foobar'), Raw('0.5*foo + 0.5*bar')))
        self.assertEqual(score.ast(), ast)
    
    def test_linear_combination_score(self):
        foo = ValueMetric(name='foo')
        bar = ValueMetric(name='bar')
        score = LinearCombinationScore(
            name = 'foobar',
            terms = [ LinearTerm(metric=foo, coeff=0.5), 
                      LinearTerm(metric=bar, coeff=0.5) ],
        )
        ast = Call(Name('def_composite_score'),
                  (Name('foobar'),
                   Call(Name('+'),
                        Call(Name('*'), Constant(0.5), Name('foo')),
                        Call(Name('*'), Constant(0.5), Name('bar')))))
        self.assertEqual(score.ast(), ast)


if __name__ == '__main__':
    unittest.main()
