from __future__ import absolute_import

from traits.api import Bool, Int, Float, Str
import pandas as pd

from ..variable import Variable

    
sample_data = pd.DataFrame(
    [ [2, 'a', 0.0, True],
      [1, 'a', 0.5, False],
      [3, 'b', 1.0, True] ],
    columns = ['id', 'foo', 'bar', 'baz' ])

# The variable specifications that should be inferred from the sample data.
sample_variables = [
    Variable('id', type = Int, is_numerical = True),
    Variable('foo', type = Str, is_numerical = False),
    Variable('bar', type = Float, is_numerical = True),
    Variable('baz', type = Bool, is_numerical = True),
]