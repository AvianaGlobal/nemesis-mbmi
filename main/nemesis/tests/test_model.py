from __future__ import absolute_import

import unittest

from nemesis.model import ModelError
from nemesis.tests.system_tests import preparer_model


class TestModel(unittest.TestCase):
    
    def test_validate_correct(self):
        """ Does a correct model validate without errors?
        """
        preparer_model.validate()

    def test_validate_toplevel_names(self):
        """ Model validation: are missing entity/group names detected?"
        """
        model = preparer_model.clone_traits()
        model.entity_name = ''
        self.assertRaises(ModelError, model.validate)
        
        model = preparer_model.clone_traits()
        model.group_name = ''
        self.assertRaises(ModelError, model.validate)
    
    def test_validate_unique_names(self):
        """ Model validation: are duplicated names detected?
        """
        model = preparer_model.clone_traits(copy='deep')
        model.metrics[0].name = 'foo'
        model.metrics[1].name = 'foo'
        self.assertRaises(ModelError, model.validate)


if __name__ == '__main__':
    unittest.main()