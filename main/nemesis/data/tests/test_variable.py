from __future__ import absolute_import

import unittest

from ..variable import Variable
from .sample_data import sample_data, sample_variables


class TestVariable(unittest.TestCase):

    def test_from_data_frame(self):
        variables = Variable.from_data_frame(sample_data, statistics=True)
        self.assertEqual(variables, sample_variables)
        
        # Categorical variable.
        foo_var = variables[1]
        self.assertFalse(foo_var.is_numerical)
        self.assertEqual(foo_var.statistics['count'], len(sample_data))
        self.assertEqual(foo_var.statistics['top'], 'a')
        
        # Numerical variable.
        bar_var = variables[2]
        self.assertTrue(bar_var.is_numerical)
        self.assertEqual(bar_var.statistics['mean'], sample_data['bar'].mean())
        self.assertEqual(bar_var.statistics['std'], sample_data['bar'].std())


if __name__ == '__main__':
    unittest.main()