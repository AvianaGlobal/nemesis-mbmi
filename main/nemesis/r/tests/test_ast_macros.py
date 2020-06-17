from __future__ import absolute_import

import unittest
from ..ast import Constant, Name, Call
from ..ast_macros import Sum, Product, seq_to_list, seq_to_vector


class TestASTMacros(unittest.TestCase):
    
    def test_arithmetic_macros(self):
        self.assertEqual(Sum(), Constant(0))
        self.assertEqual(Sum(Constant(1)), Constant(1))
        self.assertEqual(Sum(Constant(1), Constant(2)),
                         Call(Name('+'), Constant(1), Constant(2)))
        self.assertEqual(Sum(Constant(1), Constant(2), Constant(3)),
                         Call(Name('+'),
                              Call(Name('+'), Constant(1), Constant(2)),
                              Constant(3)))
                              
        self.assertEqual(Product(), Constant(1))
        self.assertEqual(Product(Constant(1), Constant(2)),
                         Call(Name('*'), Constant(1), Constant(2)))

    def test_seq_to_list(self):
        self.assertEqual(seq_to_list([]), Call(Name('list')))
        self.assertEqual(seq_to_list([1]), Call(Name('list'), Constant(1)))

    def test_seq_to_vector(self):
        self.assertEqual(seq_to_vector([]), Call(Name('c')))
        self.assertEqual(seq_to_vector([1]), Constant(1))
        self.assertEqual(seq_to_vector([1,2]),
                         Call(Name('c'), Constant(1), Constant(2)))


if __name__ == '__main__':
    unittest.main()
