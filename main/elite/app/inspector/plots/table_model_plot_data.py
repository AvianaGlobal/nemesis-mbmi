from chaco.api import AbstractPlotData
from traits.api import Instance

from elite.data.ui.base_table_model import BaseTableModel


class TableModelPlotData(AbstractPlotData):
    """ A chaco PlotData source for pandas DataFrames.
    """ 
        
    # The pandas DataFrame.
    model = Instance(BaseTableModel)
    
    # AbstractPlotData interface.
    
    writable = False
    selectable = False

    def list_data(self):
        """ Returns a list of valid names to use for get_data().

        These names are generally strings but can also be integers or any other
        hashable type.
        """
        if self.model is None:
            return []
        else:
            return self.model.get_columns()

    def get_data(self, name):
        """ Returns the data or data source associated with *name*.

        If there is no data or data source associated with the name, this method
        returns None.
        """
        if self.model is None or name not in self.model.get_columns():
            return []
        else:
            j = self.list_data().index(name)
            return [self.model.get_value(i, j)
                    for i in range(self.model.rowCount())]

    # Private interface
    
    def _model_changed(self, old, new):
        event = {}
        if old is not None:
            event['removed'] = old.get_columns()
        if new is not None:
            event['added'] = new.get_columns()
        self.data_changed = event