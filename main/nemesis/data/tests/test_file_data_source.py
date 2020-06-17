from __future__ import absolute_import

import os.path
import unittest
from pandas.util.testing import assert_frame_equal

from nemesis.r.ast import Call, Name, Constant
from ..file_data_source import FileDataSource
from .sample_data import sample_data, sample_variables


class TestFileDataSource(unittest.TestCase):

    def _test_load_file_type(self, ext, check_types=True):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        path = os.path.join(data_dir, 'sample_data' + ext)
        ds = FileDataSource(path=path)
        
        self.assertTrue(ds.can_load)
        ds.load_metadata()
        if check_types:
            self.assertEqual(ds.variables, sample_variables)
        else:
            self.assertEqual([v.name for v in ds.variables],
                             [v.name for v in sample_variables])
        
        loaded = ds.load()
        assert_frame_equal(loaded, sample_data, check_dtype=check_types)
        
        cols = ['foo','bar']
        loaded = ds.load(variables = cols)
        assert_frame_equal(loaded, sample_data[cols], check_dtype=check_types)
        
        ds.limit_rows = True
        ds.num_rows = 2
        loaded = ds.load()
        assert_frame_equal(loaded, sample_data[:2], check_dtype=check_types)
        
    def test_ast_csv(self):
        ds = FileDataSource(path='foo.csv')
        self.assertEqual(ds.ast(), Constant('foo.csv'))
    
    def test_ast_tsv(self):
        ds = FileDataSource(path='foo.tab')
        self.assertEqual(ds.ast(), Constant('foo.tab'))
                         
    def test_ast_xls(self):
        ds = FileDataSource(path='foo.xls')
        target = Call(Name('read.xlsx'), Constant('foo.xls'), Constant(1))
        self.assertEqual(ds.ast(), target)
    
    def test_ast_rds(self):
        ds = FileDataSource(path='foo.RDS')
        target = Call(Name('readRDS'), Constant('foo.RDS'))
        self.assertEqual(ds.ast(), target)

    def test_load_csv(self):
        self._test_load_file_type('.csv')

    def test_load_tsv(self):
        self._test_load_file_type('.tsv')

    def test_load_excel(self):
        self._test_load_file_type('.xlsx')
    
    def test_file_types(self):
        ds = FileDataSource()
        self.assertTrue('.csv' in ds.file_types)
        self.assertFalse('.txt' in ds.file_types)
    
    def test_wildcard(self):
        ds = FileDataSource()
        self.assertTrue('Comma-separated (*.csv)' in ds.wildcard)
        self.assertTrue('Tab-separated (*.tsv *.tab)' in ds.wildcard)


if __name__ == '__main__':
    unittest.main()
