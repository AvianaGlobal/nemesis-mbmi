from traits.api import HasTraits


class DeepEqualityAssertions(object):
    """ Mixin class for TestCase providing deep equality assertions.
    """
    
    def assert_deep_equality(self, first, second):
        """ Check for "deep" equality of two objects.
        
        Non-builtin object types are assumed to derive from HasTraits. 
        """
        if isinstance(first, basestring):
            # Ignore differences between `str` and `unicode`.
            self.assertTrue(isinstance(second, basestring))
        else:
            self.assertEqual(first.__class__, second.__class__)
        
        if isinstance(first, HasTraits):
            for name in first.copyable_trait_names():
                self.assert_deep_equality(getattr(first, name),
                                          getattr(second, name))
                                          
        elif isinstance(first, list):
            self.assertEqual(len(first), len(second))
            for i in xrange(len(first)):
                self.assert_deep_equality(first[i], second[i])            
        
        elif isinstance(first, dict):
            self.assertEqual(first.viewkeys(), second.viewkeys())
            for key in first.iterkeys():
                self.assert_deep_equality(first[key], second[key])

        else:
            self.assertEqual(first, second)