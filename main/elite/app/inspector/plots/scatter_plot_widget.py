from __future__ import absolute_import

import numpy as np

# Monkeypatch points_in_polygon to fix an incompatibility between numpy >= 1.10
# and chaco. points_in_polygon returns an ndarray of dtype int32 and chaco
# attempts to OR this with an ndarray of dtype bool. In the most recent
# versions of numpy, this implicit casting raises an exception.
from kiva import agg
_points_in_polygon = agg.points_in_polygon

def patched_points_in_polygon(*args, **kwargs):
    results = _points_in_polygon(*args, **kwargs)
    return results.astype(np.bool_)

agg.points_in_polygon = patched_points_in_polygon

from atom.api import Atom, Bool, Enum, List, Typed, ForwardTyped, set_default
from enaml.core.api import d_
from enable.api import KeySpec
from chaco.api import (Plot, PlotComponent, LassoOverlay,
                       ScatterInspectorOverlay, DataLabel)
from chaco.tools.api import PanTool, ZoomTool, LassoSelection, ScatterInspector

from traits.api import Instance

from elite.data.ui.base_table_model import BaseTableModel
from .chaco_canvas import ChacoCanvas
from .drop_axis import DropAxis
from .editable_plot import EditablePlot, PlotSettings
from .table_model_plot_data import TableModelPlotData


class ScatterPlotWidget(ChacoCanvas, EditablePlot):

    # The data to display
    model = d_(Typed(BaseTableModel))
    
    # The currently selected points.
    selected = d_(List())
    
    # The currently active tool.
    tool = d_(Enum('pointer', 'lasso', 'zoom'))
    
    # The underlying scatter plot.
    scatter = Typed(PlotComponent)

    # The id of the editor widget in the ObjectRegistry
    editor_id = set_default('scatter_plot_editor')

    # Internal state.
    _selection_updating = Bool(False)
    _tool = ForwardTyped(lambda: ScatterPlotTool)
    _zoom_tool = Typed(ZoomTool)

    # RawWidget interface.
    
    def create_widget(self, parent):
        self._create_plot_component()
        return super(ScatterPlotWidget, self).create_widget(parent)

    # Editable plot interface

    def _default_settings(self):
        return PlotSettings(title=u'Group Scatter Plot')

    def _observe_settings(self, change):
        super(ScatterPlotWidget, self)._observe_settings(change)
        if change['type'] == 'create':
            self.save_settings()

    def restore_settings(self):
        super(ScatterPlotWidget, self).restore_settings()
        self._zoom_tool._reset_state_pressed()

    # Private interface.
    
    def _create_plot_component(self):
        plot_data = TableModelPlotData(model = self.model)

        self.component = plot = Plot(plot_data,
            auto_axis = False,
            padding_left = 75, # FIXME: Can Chaco calcuate this automatically?
        )
        plot.x_axis = DropAxis(component = plot, mapper = plot.x_mapper,
                               plot_name = 'x', orientation = 'bottom')

        plot.y_axis = DropAxis(component = plot, mapper = plot.y_mapper,
                               plot_name = 'y', orientation = 'left')

        self.scatter = scatter = plot.plot(('x', 'y'), 
            type = 'scatter',
            marker = 'circle',
        )[0]
        plot.title = self.settings.title
        
        # Create selection overlay.
        inspector_overlay = SafeScatterInspectorOverlay(self.model,
            scatter,
            selection_metadata_name = 'selection',
            selection_color = 'blue',
            selection_marker_size = 6,
        )
        scatter.overlays.append(inspector_overlay)
        
        # Create standard tools (always active).
        scatter.tools.append(PanTool(scatter, drag_button = 'right'))

        self._zoom_tool = ZoomTool(scatter,
           drag_button=None,
           enter_zoom_key=KeySpec(None),
           exit_zoom_key=KeySpec(None)
        )
        scatter.tools.append(self._zoom_tool)
        
        # Create the active selection and tool.
        self._set_selection(self.selected)
        self._set_tool(self.tool)
        
        # Register event handlers.
        scatter.index.on_trait_change(self._update_selection,
                                      'metadata_changed')

    def _set_selection(self, selected):
        self._selection_updating = True
        try:
            metadata = self.scatter.index.metadata
            metadata['selection'] = map(self.model.map_from_row, selected)
        finally:
            self._selection_updating = False
    
    def _set_tool(self, tool_name):
        # Remove old tool, if necessary.
        if self._tool:
            self._tool.remove()
            self._tool = None
        
        # Install new tool.
        tool_cls = scatter_plot_tools[tool_name]
        self._tool = tool_cls(widget = self)
        self._tool.install()
    
    # Attribute change handlers

    def _update_selection(self):
        if self._selection_updating:
            return
        self._selection_updating = True
        try:
            metadata = self.scatter.index.metadata
            self.selected = [
                self.model.map_to_row(s) for s in metadata.get('selection', [])
            ]
        finally:
            self._selection_updating = False
    
    def _observe_selected(self, change):
        if not self._selection_updating and change['type'] == 'update':
            self._set_selection(change['value'])
    
    def _observe_tool(self, change):
        if change['type'] == 'update':
            self._set_tool(change['value'])

    def _observe_model(self, change):
        if 'oldvalue' in change:
            change['oldvalue'].dataChanged.disconnect(self.update_from_model)
        change['value'].dataChanged.connect(self.update_from_model)

    def update_from_settings(self):
        self.component.title = self.settings.title
        self._window.control.update()

    def update_from_model(self):
        self.component.x_axis.refresh_data()
        self.component.y_axis.refresh_data()
        self._set_selection(self.selected)


class SafeScatterInspectorOverlay(ScatterInspectorOverlay):

    _hover_label = Instance(DataLabel)

    def __init__(self, model, *args, **kwargs):
        super(SafeScatterInspectorOverlay, self).__init__(*args, **kwargs)
        self.model = model
    
    def overlay(self, component, gc, view_bounds=None, mode='normal'):
        """ Reimplemented to skip rendering if there is no index or value data.
        """
        plot = self.component
        if not plot or not plot.index or not plot.value or \
                len(plot.index.get_data()) == 0 or \
                len(plot.value.get_data()) == 0:
            return
        return super(SafeScatterInspectorOverlay, self).overlay(
            component, gc, view_bounds, mode)

    def metadata_changed(self, object, name, old, new):
        """ Reimplemented to remove the hover label if there is no point being
        hovered over.
        """
        plot = self.component
        metadata = plot.index.metadata
        if 'hover' not in metadata and self._hover_label is not None:
            plot.overlays.remove(self._hover_label)
            self._hover_label = None

        super(SafeScatterInspectorOverlay, self).metadata_changed(object, name, old, new)

    def _render_at_indices(self, gc, screen_pts, inspect_type):
        """ Reimplemented to render a data label on hover.
        """
        if inspect_type == 'hover':
            plot = self.component

            if self._hover_label is not None:
                plot.overlays.remove(self._hover_label)
                self._hover_label = None

            point = plot.map_data(screen_pts[0])

            group_index = plot.map_index(screen_pts[0], threshold=5.0)
            group = self.model.map_to_row(group_index)
            label = DataLabel(component=plot, data_point=point,
                              label_text='Group %s' % group, marker='circle',
                              show_label_coords=False)
            plot.overlays.append(label)
            self._hover_label = label

        else:
            super(SafeScatterInspectorOverlay, self)._render_at_indices(gc, screen_pts, inspect_type)


class ScatterPlotTool(Atom):
    __slots__ = '__weakref__'

    widget = Typed(ScatterPlotWidget)
        
    def install(self):
        """ Create the tool and add it to the widget.
        """
        raise NotImplementedError
        
    def remove(self):
        """ Remove the tool from the widget.
        """
        raise NotImplementedError


class ScatterPlotPointerTool(ScatterPlotTool):
    
    _tool = Typed(ScatterInspector)
    
    def install(self):
        scatter = self.widget.scatter
        self._tool = ScatterInspector(scatter,
            selection_metadata_name = 'selection',
            selection_mode = 'toggle',
        )
        scatter.tools.append(self._tool)
        
    def remove(self):
        self.widget.scatter.tools.remove(self._tool)


class ScatterPlotLassoTool(ScatterPlotTool):
    
    _tool = Typed(LassoSelection)
    _overlay = Typed(LassoOverlay)
    
    def install(self):
        scatter = self.widget.scatter
        self._tool = tool = LassoSelection(scatter,
            drag_button = 'left',
            selection_datasource = scatter.index,
            metadata_name = 'lasso_selection',
        )
        tool.on_trait_change(self._selection_changed, 'selection_changed')
        
        self._overlay = LassoOverlay(scatter,
            lasso_selection = self._tool,
        )
        scatter.tools.append(self._tool)
        scatter.overlays.append(self._overlay)
    
    def remove(self):
        scatter = self.widget.scatter
        scatter.tools.remove(self._tool)
        scatter.overlays.remove(self._overlay)
    
    def _selection_changed(self):
        """ Translate lasso selection format to inspector selecton format.
        """
        tool = self._tool
        mask = tool.selection_datasource.metadata[tool.metadata_name]
        metadata = self.widget.scatter.index.metadata
        metadata['selection'] = list(np.where(mask)[0])


class ScatterPlotZoomTool(ScatterPlotTool):
    
    _tool = Typed(ZoomTool)
    
    def install(self):
        scatter = self.widget.scatter
        self._tool = ZoomTool(scatter, always_on = True)
        scatter.overlays.append(self._tool)
    
    def remove(self):
        self.widget.scatter.overlays.remove(self._tool)


scatter_plot_tools = {
    'pointer' : ScatterPlotPointerTool,
    'lasso': ScatterPlotLassoTool,
    'zoom': ScatterPlotZoomTool,
}
