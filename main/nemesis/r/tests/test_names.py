from __future__ import absolute_import

import unittest
from ..names import is_reserved, is_syntactic_name, is_name


class TestRNames(unittest.TestCase):

    def test_is_reserved(self):
        self.assertTrue(is_reserved('if'))
        self.assertTrue(is_reserved('NA'))
        self.assertTrue(is_reserved('...'))
        self.assertTrue(is_reserved('..2'))
        self.assertFalse(is_reserved('foo'))
        self.assertFalse(is_reserved('..2a'))

    def test_is_syntactic_name(self):
        self.assertTrue(is_syntactic_name('foo'))
        self.assertTrue(is_syntactic_name('foo.bar'))
        self.assertFalse(is_syntactic_name('foo bar'))
        self.assertTrue(is_syntactic_name('.'))
        self.assertTrue(is_syntactic_name('...'))
        self.assertTrue(is_syntactic_name('if'))

    def test_is_assignable_name(self):
        self.assertTrue(is_name('foo'))
        self.assertTrue(is_name('foo.bar'))
        self.assertFalse(is_name('foo bar'))
        self.assertTrue(is_name('.'))
        self.assertFalse(is_name('...'))
        self.assertFalse(is_name('if'))


if __name__ == '__main__':
    unittest.main()
