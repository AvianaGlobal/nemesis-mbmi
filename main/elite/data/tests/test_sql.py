from __future__ import absolute_import

import os.path
import unittest

import numpy as np
import pandas as pd
from pandas.util.testing import assert_frame_equal
import sqlalchemy

from ..sql import read_sql_table, sample_sql_table
from .sample_data import sample_data


class TestSqlFunctions(unittest.TestCase):
    
    def test_read_table_sqlite(self):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        path = os.path.join(data_dir, 'sample_data.db')
        engine = sqlalchemy.create_engine('sqlite:///{path}'.format(path=path))
        name = 'sample_tbl'
        
        loaded = read_sql_table(engine, name)
        assert_frame_equal(loaded, sample_data)
        
        loaded = read_sql_table(engine, name, limit=2)
        assert_frame_equal(loaded, sample_data[:2])
        
        cols = ['foo','bar']
        loaded = read_sql_table(engine, name, columns=cols)
        assert_frame_equal(loaded, sample_data[cols])
        
        loaded = read_sql_table(engine, name, index_col='id')
        assert_frame_equal(loaded, sample_data.set_index('id'))
        
        loaded = read_sql_table(engine, name, index_col='id', columns=cols)
        assert_frame_equal(loaded, sample_data.set_index('id')[cols])
        
        # Simple WHERE clauses.
        standardize = lambda df: df.sort('id').reset_index(drop=True)
        
        target = sample_data.query('baz == 1')
        loaded = read_sql_table(engine, name, where='baz = 1')
        assert_frame_equal(standardize(loaded), standardize(target))
        
        where = sqlalchemy.text('baz = :baz').bindparams(baz = 1)
        loaded = read_sql_table(engine, name, where=where)
        assert_frame_equal(standardize(loaded), standardize(target))
        
        # WHERE IN clauses.
        target = sample_data.query('id in [1,2]')
        loaded = read_sql_table(engine, name, where='id IN (1,2)')
        assert_frame_equal(standardize(loaded), standardize(target))
        
        where = sqlalchemy.sql.column('id').in_([1,2])
        loaded = read_sql_table(engine, name, where=where)
        assert_frame_equal(standardize(loaded), standardize(target))
    
    def test_sample_table_sqlite(self):
        engine = sqlalchemy.create_engine('sqlite:///:memory:')
        n = 1000
        df = pd.DataFrame({
            'id': np.arange(n),
            'x': np.random.uniform(size=n),
        })
        df.to_sql('tbl', engine, index=False)
        
        sampled = sample_sql_table(engine, 'tbl', 100)
        self.assertEqual(len(sampled), 100)
        
        sampled = sample_sql_table(engine, 'tbl', 1100)
        self.assertEqual(len(sampled), 1000)


if __name__ == '__main__':
    unittest.main()
