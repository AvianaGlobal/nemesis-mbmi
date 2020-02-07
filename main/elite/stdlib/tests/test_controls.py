from __future__ import absolute_import

import unittest

from elite.r.ast import Constant, Name, Call, Raw
from ..controls import FactorControl, NumericalControl


class TestControls(unittest.TestCase):

    def test_factor_control(self):
        control = FactorControl(name = 'gender', expression = 'GENDER')
        ast = Call(Name('def_control'), 
                   (Name('gender'), Raw('GENDER')))
        self.assertEqual(control.ast(), ast)

    def test_numerical_control(self):
        breaks = [ 0, 30, 60, 90, 120 ]
        control = NumericalControl(name = 'age_bin', expression = 'age',
                                   auto_breaks = False, breaks = breaks)
        ast = Call(Name('def_control'),
                   (Name('age_bin'),
                    Call(Name('cut'), Raw('age'),
                         (Name('breaks'),
                          Call(Name('c'), map(Constant, breaks))),
                         (Name('right'), Constant(False)))))
        self.assertEqual(control.ast(), ast)
        
        control.auto_breaks = True
        control.num_breaks = 5
        control.closed_on_left = False
        ast = Call(Name('def_control'),
                   (Name('age_bin'),
                    Call(Name('cut'), Raw('age'),
                         (Name('breaks'), Constant(5)))))
        self.assertEqual(control.ast(), ast)


if __name__ == '__main__':
    unittest.main()
