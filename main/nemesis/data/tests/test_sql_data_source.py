from __future__ import absolute_import

import os.path
import unittest

from pandas.util.testing import assert_frame_equal

from nemesis.r.ast import Call, Name, Constant
from ..sql_data_source import SQLDataSource
from .sample_data import sample_data, sample_variables


class TestSqlDataSource(unittest.TestCase):
    
    def test_ast_mysql(self):
        ds = SQLDataSource(
            dialect = 'mysql',
            host = 'example.com',
            user = 'frodo',
            password = 'friend',
            database = 'sample_data',
            table = 'sample_tbl',
        )
        nodes = [
            (Name('input'),
             Call(Name('dbConnect'),
                  Call(Name('dbDriver'), Constant('MySQL')),
                  (Name('dbname'), Constant('sample_data')),
                  (Name('user'), Constant('frodo')),
                  (Name('password'), Constant('friend')),
                  (Name('host'), Constant('example.com')))),
            (Name('input_table'),
             Constant('sample_tbl')),
        ]
        self.assertEqual(ds.ast(), nodes)
    
    def test_ast_sqllite(self):
        ds = SQLDataSource(
            dialect = 'sqlite',
            database = 'sample_data.db',
            table = 'sample_tbl',
        )
        nodes = [
            (Name('input'),
             Call(Name('dbConnect'), 
                  Call(Name('dbDriver'), Constant('SQLite')),
                  (Name('dbname'), Constant('sample_data.db')))),
            (Name('input_table'),
             Constant('sample_tbl')),
        ]
        self.assertEqual(ds.ast(), nodes)
    
    def test_load_sqllite(self):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        path = os.path.join(data_dir, 'sample_data.db')
        ds = SQLDataSource(
            dialect = 'sqlite',
            database = path,
            table = 'sample_tbl',
        )
        
        self.assertTrue(ds.can_load)
        ds.load_metadata()
        self.assertEqual(ds.variables, sample_variables)
        
        loaded = ds.load()
        assert_frame_equal(loaded, sample_data)
        
        cols = ['foo','bar']
        loaded = ds.load(variables = cols)
        assert_frame_equal(loaded, sample_data[cols])
        
        ds.limit_rows = True
        ds.num_rows = 2
        loaded = ds.load()
        assert_frame_equal(loaded, sample_data[:2])


if __name__ == '__main__':
    unittest.main()
