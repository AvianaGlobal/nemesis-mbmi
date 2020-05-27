import unittest

from ..parse import is_expression


class TestRParse(unittest.TestCase):
    
    def test_is_expression(self):
        self.assertTrue(is_expression('x'))
        self.assertTrue(is_expression('x+y'))
        self.assertTrue(is_expression('foo()'))
        self.assertFalse(is_expression('x; y'))
        self.assertFalse(is_expression('foo('))


if __name__ == '__main__':
    unittest.main()