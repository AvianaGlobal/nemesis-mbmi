from __future__ import absolute_import
from traits.api import HasTraits, Bool, List, Range
from nemesis.data.variable import Variable

class DataSource(HasTraits):
    """ An (abstract) data source that can be loaded in both R and Python.
    """
    
    # The variables (column names) in the data source.
    variables = List(Variable)
    
    # Whether data can be loaded.
    can_load = Bool(False)
    
    # Whe
    # class DataSource(HasTraitther to limit the numbers of rows loaded.
    # This does not apply to the ast() method, only to load().
    limit_rows = Bool(False)
    num_rows = Range(low=1, value=1000)
    
    def ast(self):
        """ Generate R code (as an AST) for loading the data.
        
        Returns an argument (or list of arguments) as AST(s) to be passed to
        the execution engine.
        """
        raise NotImplementedError

    def load(self, variables = None):
        """ Loads data from the data source.
        
        Parameters
        ----------
        variables : sequence of str
            Variables (columns) to load. If omitted, all variables are loaded.
        
        Returns
        -------
        A pandas data frame.
        """
        raise NotImplementedError
    
    def load_metadata(self):
        """ Loads metadata from the data source.
        
        Populates the `variables` attribute.
        """
        raise NotImplementedError
