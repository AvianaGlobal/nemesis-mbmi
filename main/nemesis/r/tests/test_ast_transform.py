from __future__ import absolute_import

import unittest

from ..ast import Call, Name, Constant, Block
from ..ast_transform import find_libraries, traverse_ast


class TestFileDataSource(unittest.TestCase):
    
    def test_find_libraries(self):
        node = Call(Name('foo'),
                    Call(Name('bar'), Constant(0), libraries=['Bar']),
                    libraries=['Foo'])
        self.assertEqual(find_libraries(node), ['Foo', 'Bar'])
    
    def test_traverse(self):
        node = Block([
            Call(Name('foo'), Constant(0), Constant(1)),
        ])
    
        count = 0
        for child in traverse_ast(node, depth_first=True):
            count += 1
        self.assertEqual(count, 5)
        
        count = 0
        for child in traverse_ast(node, depth_first=False):
            count += 1
        self.assertEqual(count, 5)


if __name__ == '__main__':
    unittest.main()
