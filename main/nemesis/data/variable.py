from __future__ import absolute_import

from traits.api import HasStrictTraits, Any, Bool, Dict, Str, Type, Int, Float


R_CLASS_TO_TRAIT = {
    'logical': Bool,
    'character': Str,
    'numeric': Float,
    'integer': Int
}


class Variable(HasStrictTraits):
    """ Represents a variable in a data set.
    
    Typically corresponds to a column in a flat file or SQL database.
    """

    # The name of the variable.
    name = Str()
    
    # The type of the variable, represented as a TraitType.
    # We use a TraitType instead of a NumPy dtype or SQL data type to avoid a 
    # coupling to any particular data source.
    type = Type()
    
    # Whether the variable is categorical or numerical.
    # By default, this is inferred from the ``type`` attribute and boolean
    # types are treated as numerical.
    is_numerical = Bool()
    
    # An object identifying the source of a variable, e.g., a filename or a
    # SQL table name.
    source = Any()
    
    # Summary statistics for the variable.
    statistics = Dict(Str, Any)
    
    def __init__(self, name, type, **traits):
        super(Variable, self).__init__(name=name, type=type, **traits)

    def __repr__(self):
        type_str = 'None' if self.type is None else self.type.__name__
        return 'Variable({0}, {1})'.format(repr(self.name), type_str)

    def __eq__(self, other):
        return (isinstance(other, Variable) and
                self.name == other.name and self.type == other.type and
                self.is_numerical == other.is_numerical and
                self.source == other.source)
    
    def _is_numerical_default(self):
        from traits.api import BaseStr
        return not issubclass(self.type, BaseStr)
    
    @classmethod
    def from_data_frame(cls, df, statistics=False, **traits):
        """ Extract a list of Variables from a pandas DataFrame.
        """
        variables = []
        for col, dtype in zip(df.columns, df.dtypes):
            var = cls.from_dtype(col, dtype, **traits)
            if statistics:
                var.statistics = dict(df[col].describe())
            variables.append(var)
        return variables

    @classmethod
    def from_metadata(cls, df, type, **traits):
        """ Extract a list of Variables from a metadata table.
        """
        variables = []

        of_type = df[df['type'] == type]
        for _, row in of_type.iterrows():
            name = row['name']
            type = R_CLASS_TO_TRAIT[row['dtype']]
            variables.append(cls(name, type, **traits))

        return variables
                
    @classmethod
    def from_dtype(cls, name, dtype, **traits):
        from traits.trait_numeric import dtype2trait
        if dtype.name == 'bool':
            type = Bool
        elif dtype.name == 'object':
            type = Str
        else:
            type = dtype2trait(dtype)
        return cls(name, type, **traits)