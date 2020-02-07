from __future__ import absolute_import

import math

from matplotlib import pyplot
import pandas as pd

from atom.api import Bool, Dict, List, Typed, Str, observe, set_default
from enaml.core.api import d_, d_func
from enaml.widgets.api import Feature, MPLCanvas
from traitsui.qt4.clipboard import PyMimeData

from elite.ui.file_dialog import FileDialogEx, file_type_filters
from elite.ui.message_box import warning
from .editable_plot import EditablePlot, XYPlotSettings
from .plot_limits import PlotLimits


class MatplotlibWidget(MPLCanvas, EditablePlot):
    """ An Enaml widget for displaying pandas/matplotlib plots of grouped
    and population data.
    """
    # MatplotlibWidget interface.
    
    # The data to display.
    data_frame = d_(Typed(pd.DataFrame))
    data_columns = d_(List(Str()))
    
    # Optional metadata. For tracking purposes only; not used by the widget.
    data_info = d_(Dict(Str()))
    
    # Optional column for comparing distributions of sub-populations.
    group_by = d_(Str())
    
    # Whether the widget supports plotting multiple columns at once.
    # If false, then ``data_columns`` should have length at most 1.
    multi_column = Bool(False)

    # Widget interface.

    # Allow drops.
    features = set_default(Feature.DropEnabled)
    
    # Allow the canvas to shrink freely.
    resist_width = set_default('ignore')
    resist_height = set_default('ignore')
    
    # Private interface.
    
    # A lock to prevent observed notifications when limits are updated from
    # the default axes values
    _limit_lock = Bool(False)

    # Flag indicating whether the user has edited the limits of the plot
    _limits_edited = Bool(False)

    # ToolkitObject interface.
    
    def initialize(self):
        super(MatplotlibWidget, self).initialize()
        self.reload_figure()
    
    # Widget interface.
    
    def drag_enter(self, event):
        accept = False
        mime_data = event.mime_data()
        
        if mime_data.has_format(PyMimeData.MIME_TYPE):
            data = PyMimeData.coerce(mime_data.q_data()).instance()
            accept = self.validate_drag_enter(data)
        
        if accept:
            event.accept_proposed_action()
    
    def drop(self, event):
        accept = False
        mime_data = event.mime_data()
        
        if mime_data.has_format(PyMimeData.MIME_TYPE):
            data = PyMimeData.coerce(mime_data.q_data()).instance()
            accept = self.load_drop(data)
        
        if accept:
            event.accept_proposed_action()

    # Editable plot interface

    def _default_settings(self):
        return XYPlotSettings()

    def can_edit(self):
        return self.data_frame is not None and len(self.data_columns) > 0

    # MatplotlibWidget interface
    
    def reload_figure(self):
        """ Create (or recreate) the figure.
        
        Note that this function is *not* called automatically when 
        ``data_frame``, ``data_columns``, etc are changed.
        """
        # Close old figure so that it can be disposed of.
        if self.figure is not None:
            pyplot.close(self.figure)
            
        # Create new figure. We specify our own layout parameters instead of
        # using tight_layout because tight_layout triggers a bug in the
        # pandas plotting methods
        figure = pyplot.figure(facecolor = 'white')
        pyplot.subplots_adjust(left=0.05, right=0.99, top=0.95, wspace=0.1, hspace=0.4)
        pyplot.rcParams['axes.color_cycle'] = ['#b88dd8', '#808080', '#e8d9f3','#999999', '#d0e2b6',]
        
        if self.data_frame is None or not self.data_columns:
            if self.multi_column:
                title = '[Drag variables here]'
            else:
                title = '[Drag a variable here]'
            figure.suptitle(title)
        else:
            axes = self._create_plot(figure)
            if not self._limits_edited:
                self._update_limits_from_axes(axes)
            else:
                self._update_limits_from_settings(axes)

            figure.suptitle(self.settings.title)

            self.save_settings()

        self.figure = figure
    
    def reset_figure(self):
        """ Reload the figure, discarding any user settings.
        """
        self._limits_edited = False
        self.clear_settings()
        self.reload_figure()
    
    @d_func
    def validate_drag_enter(self, drag_data):
        """ Validate the drag data, a list of drag objects.
        
        By default, each drag object is assumed to be a column name and is
        checked against the data frame.
        """
        df = self.data_frame
        return (isinstance(drag_data, list) and
                (len(drag_data) == 1 or self.multi_column) and
                df is not None and
                all(x in df.columns for x in drag_data))
    
    @d_func
    def validate_drop(self, data_frame, columns):
        """ Validate the data loaded from a drop.
        """
        return True
    
    @d_func
    def load_drop(self, drag_data):
        """ Load data from a drop.
        
        By default, uses the data frame already assigned to this object.
        """
        if self.validate_drop(self.data_frame, drag_data):
            self.data_columns = drag_data
            return True
        return False
    
    def save(self):
        """ Show a dialog for saving the figure.
        
        Returns whether the figure was successfully saved.
        """
        # Adapted from ``matplotlib.backends.backend_qt5``
        canvas = self.figure.canvas
        filetypes = canvas.get_supported_filetypes_grouped()
        default_filetype = canvas.get_default_filetype()

        name_filters, selected_name_filter = file_type_filters(
            filetypes, default=default_filetype
        )

        filename = FileDialogEx.get_save_file_name(
            parent = self,
            name_filters = name_filters,
            selected_name_filter = selected_name_filter
        )

        if filename:
            try:
                canvas.print_figure(filename)
            except Exception as exc:
                warning(parent = self.parent,
                        title = 'Save Error',
                        text = 'Error saving figure',
                        content = str(exc))
            else:
                return True
        return False
    
    # Protected interface

    def _create_plot(self, figure):
        raise NotImplementedError
    
    def _create_plot_data(self, melt=False):
        df, columns = self.data_frame, self.data_columns
        if self.group_by:
            df = df[[self.group_by]+columns]
        else:
            df = df[columns]
        if melt:
            df = pd.melt(df, id_vars=[self.group_by] if self.group_by else [])
        return df

    def _plot_layout(self, n_plots):
        per_line = round(math.sqrt(n_plots))
        return (int(per_line), int(math.ceil(n_plots / per_line)))

    def _update_limits_from_axes(self, axes):
        """ Update the current plot limits settings from an Axes object.
        """
        self._limit_lock = True
        limits = axes.axis()

        self.settings.x_limits = PlotLimits.from_tuple(limits[:2])
        self.settings.y_limits = PlotLimits.from_tuple(limits[2:])

        self._limit_lock = False
    
    # Attribute change handlers
    
    @observe('data_frame', 'data_columns', 'group_by')
    def _update_figure(self, change):
        if change['type'] == 'update':
            self.reload_figure()

    def update_from_settings(self):
        if self.figure and self.data_frame is not None and self.data_columns:
            self.figure.suptitle(self.settings.title)
            self.figure.canvas.draw()

        self._update_limits_from_settings(self.figure.gca())

    def _update_limits_from_settings(self, axes):
        """ Update the plot limits of an Axes object from the current settings.
        """
        if self._limit_lock:
            return

        limits = self.settings.x_limits.as_tuple() + self.settings.y_limits.as_tuple()
        self._limits_edited = limits != axes.axis()

        axes.axis(limits)
        self.figure.canvas.draw()
