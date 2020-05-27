from __future__ import absolute_import

import unittest
import string
import numpy as np

from ..heuristics import is_discrete


class TestHeuristics(unittest.TestCase):

    def test_is_discrete(self):
        """ Does the discreteness test work in some "obvious" cases?
        """
        self.assertTrue(is_discrete(['foo', 'bar', 'baz']))
        self.assertTrue(is_discrete(list(string.ascii_letters)))
        self.assertTrue(is_discrete([1,2,3,4,5]))
        self.assertFalse(is_discrete(np.random.uniform(5)))
        self.assertFalse(is_discrete(
            np.random.random_integers(0, 1000, size=1000)))
        

if __name__ == '__main__':
    unittest.main()
