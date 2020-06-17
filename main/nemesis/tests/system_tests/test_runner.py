from __future__ import absolute_import

import os
import unittest
import tempfile

from nemesis.data.file_data_source import FileDataSource
from nemesis.data.sql_data_source import SQLDataSource
from nemesis.runner import Runner

from .preparer_model import preparer_model

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class IntegrationTestRunner(unittest.TestCase):
    
    def setUp(self):
        f, path = tempfile.mkstemp(prefix='results_', suffix='.sqlite')
        os.close(f)
        self.output_source = SQLDataSource(dialect='sqlite', database=path)
    
    def tearDown(self):
        os.remove(self.output_source.database)
        self.output_source = None
    
    def test_model_run(self):
        """ Does executing the entire model pipeline work?
        """
        data_path = os.path.join(DATA_DIR, 'Anon_Prep_Data_1k.RDS')
        runner = Runner(
            model = preparer_model,
            input_source = FileDataSource(path = data_path),
            output_source = self.output_source,
        )
        results = runner.run_and_wait()
        
        names = lambda objs: [obj.name for obj in objs]
        self.assertTrue(results is not None)
        self.assertEqual(results.entity_name, 'Anon_Entity_ID')
        self.assertEqual(results.group_name, 'Anon_Preparer_ID')
        self.assertEqual(names(results.metric_vars),
                         names(preparer_model.metrics))
        self.assertEqual(names(results.composite_score_vars),
                         names(preparer_model.composite_scores))
    
    def test_model_run_errors(self):
        """ Are errors handled when running a model?
        """
        errors = [0]
        def error_handler(msg, detail):
            if 'No such file' in detail:
                errors[0] += 1
        
        data_path = os.path.join(DATA_DIR, 'NONEXISTENT.RDS')
        runner = Runner(
            model = preparer_model,
            input_source = FileDataSource(path = data_path),
            output_source = self.output_source,
            error_handler = error_handler,
        )
        results = runner.run_and_wait()
        self.assertTrue(results is None)
        self.assertEqual(errors[0], 1)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level = logging.DEBUG)
    
    unittest.main()
