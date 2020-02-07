from __future__ import absolute_import

import os.path
import unittest
from cStringIO import StringIO

from elite.data.file_data_source import FileDataSource
from elite.data.sql_data_source import SQLDataSource
from elite.model import Model
from elite.runner import Runner

from .assertions import DeepEqualityAssertions
from .med_ded_model import med_ded_model


class IntegrationTestRunner(unittest.TestCase, DeepEqualityAssertions):
    
    def test_serialization(self):
        """ Does the whole model object round-trip through serialization?
        """
        io = StringIO()
        med_ded_model.save(io)
        io.seek(0)
        round_tripped = Model.load(io)
        self.assert_deep_equality(med_ded_model, round_tripped)
        
        # Verify reference identity. 
        for c1, c2 in zip(round_tripped.controls,
                          round_tripped.metrics[0].control_for):
            self.assertTrue(c1 is c2)

    def test_write_program(self):
        """ Exercise the entire model generation pipeline:
                Python model -> R AST -> R code
        """
        runner = Runner(
            model = med_ded_model,
            input_source = FileDataSource(path='Anon_Prep_Data.csv'),
            output_source = SQLDataSource(dialect='sqlite',
                                          database='results.db'),
        )
        io = StringIO()
        runner.write_program(io)
        actual = io.getvalue()

        directory = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(directory, 'data', 'med_ded_model.R')
        with file(path, 'r') as f:
            target = f.read()

        self.assertEqual(actual, target)


if __name__ == '__main__':
    unittest.main()
