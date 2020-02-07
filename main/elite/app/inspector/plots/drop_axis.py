from __future__ import absolute_import

from chaco.api import PlotAxis
from traits.api import Instance, Str

from elite.data.variable import Variable


class AbstractDropAxis(PlotAxis):
    """ A plot axis that supports dropping data names.
    """
    
    # AbstractDropAxis abstract interface
    
    def is_valid_name(self, name):
        """ Returns whether data is associated with the given name.
        """
        raise NotImplementedError
    
    def set_data(self, name):
        """ Set the data to be shown along this axis.
        """
        raise NotImplementedError

    def refresh_data(self, name):
        """ Refresh the data for the axis.
        """
        raise NotImplementedError
    
    # AbstractDropAxis concrete interface

    def get_dropped_name(self, event):
        """ If possible, extract a data name from a DragEvent.
        """
        obj = event.obj
        if isinstance(obj, list) and len(obj) == 1:
            obj = obj[0]
        if isinstance(obj, basestring):
            return obj
        elif isinstance(obj, Variable):
            return obj.name
        else:
            return None
    
    def is_valid_drop(self, event):
        """ Determine whether a DragEvent represents a valid drop.
        """
        return (self.is_in(event.x, event.y) and
                self.is_valid_name(self.get_dropped_name(event)))
    
    # Interactor interface
    
    def normal_drag_over(self, event):
        if self.is_valid_drop(event):
            event.window.set_drag_result('copy')
            event.handled = True

    def normal_dropped_on(self, event):
        if self.is_valid_drop(event):
            self.set_data(self.get_dropped_name(event))
            event.window.set_drag_result('copy')
            event.handled = True
    
    # Private interface
    
    def _title_default(self):
        return u'[Drag a variable here]'


class DropAxis(AbstractDropAxis):
    """ A simple AbstractDropAxis designed for Plot instances.
    
    It looks for data inside the Plot's data source.
    """
    
    # PlotAxis interface
    
    component = Instance('chaco.api.Plot')
    
    # DropAxis interface
    
    # The name of the plot data associated with this axis.
    plot_name = Str()

    # The name of the data that was dropped on the axis
    drop_name = Str()
    
    # AbstractDropAxis interface
    
    def is_valid_name(self, name):
        plot = self.component
        return name in plot.data.list_data()
    
    def set_data(self, name):
        plot = self.component
        plot_source = plot.datasources[self.plot_name]
        plot_source.set_data(plot.data.get_data(name))
        self.drop_name = name
        self.title = name

    def refresh_data(self):
        self.set_data(self.drop_name)
