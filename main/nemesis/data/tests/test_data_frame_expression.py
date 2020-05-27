from __future__ import absolute_import

import unittest

from pandas import DataFrame, Series
from pandas.util.testing import assert_series_equal


class TestDFExpression(unittest.TestCase):

    def setUp(self):
        self.df = DataFrame({'a': [1, 2, 3], 'b': ['foo', 'bar', 'baz']})

    def tearDown(self):
        del self.df

    def test_valid_expressions(self):
        actual = DataFrameExpression.execute(self.df, 'a >= 2')
        expected = Series([False, True, True])
        assert_series_equal(expected, actual, check_names=False)

        actual = DataFrameExpression.execute(self.df, 'b == "foo"')
        expected = Series([True, False, False])
        assert_series_equal(expected, actual, check_names=False)

        self.assertEquals(3, DataFrameExpression.execute(self.df, '1 + 2'))

    def test_invalid_expression(self):
        self.assertIsNone(DataFrameExpression.execute(self.df, 'del f'))
        self.assertIsNone(DataFrameExpression.execute(self.df, '__import__("sys")'))

    def test_helper_functions(self):
        actual = DataFrameExpression.execute(self.df, 'substring(a, "b")')
        expected = Series([False, False, False])
        assert_series_equal(expected, actual, check_names=False)

        actual = DataFrameExpression.execute(self.df, 'substring(b, "b")')
        expected = Series([False, True, True])
        assert_series_equal(expected, actual, check_names=False)

        actual = DataFrameExpression.execute(self.df, 'col("a") < 2')
        expected = Series([True, False, False])
        assert_series_equal(expected, actual, check_names=False)
