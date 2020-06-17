from __future__ import absolute_import

import unittest
from textwrap import dedent
from ..ast import Constant, Name, Call, PairList, Block, Comment, Raw
from ..pretty_print import print_ast


class TestRPrettyPrint(unittest.TestCase):
    
    def assert_print(self, node, target, *args, **kw):
        self.assertEqual(print_ast(node, *args, **kw), target)

    def test_constant(self):
        self.assert_print(Constant(0), '0')
        self.assert_print(Constant(1.0), '1.0')
        self.assert_print(Constant('foo'), "'foo'")
        self.assert_print(Constant(u'foo'), "'foo'")
        self.assert_print(Constant(True), 'TRUE')
        self.assert_print(Constant(False), 'FALSE')
        self.assert_print(Constant(float('inf')), 'Inf')
        self.assert_print(Constant(float('-inf')), '-Inf')
        self.assert_print(Constant(float('nan')), 'NA')
        self.assert_print(Constant(1+1j),
                          'complex(real = 1.0, imaginary = 1.0)')

    def test_name(self):
        self.assert_print(Name('foo'), 'foo')

    def test_call(self):
        self.assert_print(Call(Name('foo')), 'foo()')
        self.assert_print(Call(Name('foo'),Constant(0)), 'foo(0)')
        self.assert_print(Call(Name('foo'),Constant(0), Constant(1)),
                         'foo(0, 1)')
        self.assert_print(Call(Name('foo'),
                                        [(Name('bar'),Constant(0))]),
                         'foo(bar = 0)')
        self.assert_print(Call(Name('foo'),
                                        [(Name('bar'),Constant(0)),
                                         (Name('baz'),Constant(1))]),
                         'foo(bar = 0, baz = 1)')

    def test_pair_list(self):
        self.assert_print(PairList([Name('foo')]), 'foo')
        self.assert_print(PairList([Name('foo'),
                                             (Name('bar'), Constant(0))]),
                         'foo, bar = 0')

    def test_block(self):
        node = Block([Comment('Print x'),
                      Call(Name('print'), Name('x'))])
        target = dedent('''\
            # Print x
            print(x)''')
        self.assert_print(node, target)
        
        self.assert_print(Block([Name('x'), Name('y')]),
                          '  x\n  y', indent=2)

    def test_comment(self):
        # Short comment
        self.assert_print(Comment('a comment'), '# a comment')
        self.assert_print(Comment('a comment'),
                          '  # a comment', indent=2)

        # Long comment
        line1, line2 = 'a' * 50, 'b' * 50
        self.assert_print(Comment(' '.join((line1, line2))),
                          '# {}\n# {}'.format(line1, line2))

    def test_raw(self):
        self.assert_print(Raw('foo = 1'), 'foo = 1')

    def test_block_hints(self):
        node = Block([Name('x'), Name('y')])

        node.metadata['print_hint'] = 'normal'
        self.assert_print(node, 'x\ny')

        node.metadata['print_hint'] = 'short'
        self.assert_print(node, 'x; y')

        node.metadata['print_hint'] = 'long'
        self.assert_print(node, '  x\n\n  y', indent=2)

    def test_call_hints(self):
        node = Call(Name('foo'), Constant(0),
                    (Name('y'), Constant(1)), (Name('z'), Constant(2)))

        node.metadata['print_hint'] = 'normal'
        self.assert_print(node, 'foo(0, y = 1, z = 2)')

        node.metadata['print_hint'] = 'short'
        self.assert_print(node, 'foo(0,y=1,z=2)')

        node.metadata['print_hint'] = 'long'
        target = dedent('''\
           foo(0,
               y = 1,
               z = 2)''')
        self.assert_print(node, target)

        node = Call(Name('foo'),
                    Call(Name('bar'), Constant(1), Constant(2),
                         print_hint='long'))
        target = dedent('''\
            foo(bar(1,
                    2))''')
        self.assert_print(node, target)

        node = Call(Name('foo'), Constant(0),
                    Call(Name('bar'), Constant(1), Constant(2),
                         print_hint='long'),
                    print_hint = 'long')
        target = dedent('''\
            foo(0,
                bar(1,
                    2))''')
        self.assert_print(node, target)
    
    def test_arithmetic(self):
        self.assert_print(Call(Name('+'), Name('x'), Name('y')), 'x + y')
        self.assert_print(Call(Name('-'), Name('x'), Name('y')), 'x - y')
        self.assert_print(Call(Name('-'), Name('x')), '-x')
    
    def test_arithmetic_associativity(self):
        self.assert_print(Call(Name('+'),
                               Call(Name('+'), Name('x'), Name('y')),
                               Name('z')),
                          'x + y + z')
        self.assert_print(Call(Name('+'),
                               Name('x'),
                               Call(Name('+'), Name('y'), Name('z'))),
                          'x + (y + z)')
    
    def test_arithmetic_precedence(self):
        self.assert_print(Call(Name('*'),
                               Call(Name('+'), Name('x'), Name('y')),
                               Name('z')),
                          '(x + y) * z')
        self.assert_print(Call(Name('+'),
                               Name('x'),
                               Call(Name('*'), Name('y'), Name('z'))),
                          'x + y * z')
    
    def test_arithmetic_hints(self):
        node = Call(Name('+'), Name('x'), Name('y'), print_hint='short')
        self.assert_print(node, 'x+y')
    
    def test_assignment(self):
        self.assert_print(Call(Name('='), Name('x'), Constant(0)), 'x = 0')
        self.assert_print(Call(Name('<-'), Name('x'), Constant(0)), 'x <- 0')
        self.assert_print(Call(Name('<<-'), Name('x'), Constant(0)), 'x <<- 0')
    
    def test_assignment_hints(self):
        node = Call(Name('='), Name('x'), Constant(0), print_hint='short')
        self.assert_print(node, 'x=0')
    
    def test_index(self):
        self.assert_print(Call(Name('['), Name('x'), Constant(1)), 'x[1]')
        self.assert_print(Call(Name('[['), Name('x'), Constant(1)), 'x[[1]]')
    
    def test_special_operators(self):
        self.assert_print(Call(Name('%%'), Name('x'), Name('y')), 'x %% y')
        self.assert_print(Call(Name('%/%'), Name('x'), Name('y')), 'x %/% y')


if __name__ == '__main__':
    unittest.main()
