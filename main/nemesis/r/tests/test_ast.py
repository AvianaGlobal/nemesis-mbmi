from __future__ import absolute_import

import unittest
from ..ast import Constant, Name, Call, PairList


class TestAST(unittest.TestCase):

    def test_repr(self):
        self.assertEqual(repr(Constant(1.0)), "Constant(1.0)")
        self.assertEqual(repr(Name('foo')), "Name('foo')")

        call_repr = "Call(Name('foo'), [Constant(0)])"
        self.assertEqual(repr(Call(Name('foo'), Constant(0))), call_repr)
        self.assertEqual(repr(Call(Name('foo'), [Constant(0)])), call_repr)

        self.assertEqual(repr(PairList([(Name('foo'), Constant(0))])),
                         "PairList([(Name('foo'), Constant(0))])")


if __name__ == '__main__':
    unittest.main()
