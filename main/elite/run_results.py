from pandas import DataFrame
from traits.api import HasTraits, Instance, List, Property, Str

from .data.sql_data_source import SQLDataSource
from .data.variable import Variable


class RunResults(HasTraits):
    """ The results from a model run.
    """
    
    # Input data for the model run.
    # Only required if the input table is not stored in the output DB.
    input_source = Instance(SQLDataSource)
    
    # Output database from the model run. Required.
    output_source = Instance(SQLDataSource)
    
    # Run summary/metadata table. This is the only table from the output DB
    # that is automatically read and stored.
    run_summary = Instance('pandas.DataFrame')
    
    # Convenience accessors for important run metadata.
    entity_name = Property(Str, depends_on='run_summary')
    group_name = Property(Str, depends_on='run_summary')
    
    # Variables associated with input and output tables.
    input_vars = List(Variable)
    attribute_vars  = List(Variable)
    metric_vars = List(Variable)
    metric_score_vars = List(Variable)
    composite_score_vars = List(Variable)
    
    # --- RunResults interface ---
    
    def __init__(self, **traits):
        if 'output_source' not in traits:
            raise ValueError('RunResults requires an output data source')
        
        super(RunResults, self).__init__(**traits)
        
        # Load tables first so that entity and group names are available.
        self._update_tables()
        self._update_variables()

    def get_summary_data(self, key):
        """ Read a value from the run summary table.
        """
        if self.run_summary is not None:
            print('fail')
            return self.run_summary.loc[key,'value']
        return ''
    
    def load_data(self, table, **kw):
        """ Load data from an input or output table.
        """
        ds, ds_table = self._get_data_source(table)
        if ds is None:
            return DataFrame()

        if 'index_col' in kw:
            index_col = kw.pop('index_col')
        else:
            index_col = self._get_index_column(table)
        return ds.load_table(ds_table, index_col=index_col, **kw)
    
    def sample_data(self, table, n, **kw):
        """ Randomly sample from an input or output table.
        """
        ds, ds_table = self._get_data_source(table)
        if ds is None:
            return DataFrame()

        if 'index_col' in kw:
            index_col = kw.pop('index_col')
        else:
            index_col = self._get_index_column(table)
        return ds.sample_table(ds_table, n, index_col=index_col, **kw)
    
    # --- Private interface ---
    
    def _get_data_source(self, table):
        if table == 'input' and self.input_source:
            assert self.input_source.can_load
            ds = self.input_source
            ds_table = self.input_source.table
        else:
            ds = self.output_source
            ds_table = table
        return ds, ds_table
    
    def _get_index_column(self, table):
        index_map = {
            'input'                  : self.entity_name,
            'input_stats'            : 'rn',
            'run_summary'            : 'rn',
            'entity_metric_values'   : self.entity_name,
            'entity_metric_stats'    : 'rn'
        }
        return index_map.get(table)
        
    def _update_tables(self):
        if self.output_source:
            self.run_summary = self.load_data('run_summary')
        else:
            self.run_summary = None
    
    def _update_variables(self):
        
        def create_table_vars(table):
            if not self.output_source:
                return []
            df = self.load_data(table, limit = 10)
            return Variable.from_data_frame(df, source=table)

        def create_metadata_vars(table, type):
            if not self.output_source:
                return []
            df = self.load_data(table)
            return Variable.from_metadata(df, type, source=type)
        
        self.input_vars = create_table_vars('input')

        md_table = 'group_metadata'
        self.attribute_vars = create_metadata_vars(md_table, 'attribute')
        self.metric_vars = create_metadata_vars(md_table, 'metric_value')
        self.metric_score_vars = create_metadata_vars(md_table, 'metric_score')
        self.composite_score_vars = create_metadata_vars(md_table, 'composite_score')
        
        def add_stats(table_name, variables):
            if self.output_source:
                stats = self.load_data(table_name, raise_on_missing=False)
                if stats is not None:
                    for var in variables:
                        var.statistics = dict(stats.get(var.name, []))
        
        add_stats('input_stats', self.input_vars)
        add_stats('entity_metric_stats', self.metric_vars)
    
    # Trait property getter/setters
    
    def _get_entity_name(self):
        return self.get_summary_data('entity_name')
    
    def _get_group_name(self):
        return self.get_summary_data('group_name')