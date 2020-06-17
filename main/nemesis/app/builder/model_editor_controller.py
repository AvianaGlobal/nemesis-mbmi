from __future__ import absolute_import
from traits.api import Any, Instance
from traitsui.api import Handler
from nemesis.model import Control, Metric, Model, CompositeScore


class ModelEditorController(Handler):
    
    # The model being edited.
    model = Instance(Model)
    
    # The currently selected object.
    selected_object = Any()
    
    # The UI for the currently selected node.
    selected_ui = Instance('enaml.widgets.widget.Widget')

    def add_object(self, obj):
        """ Add an object to the current model.
        """
        if isinstance(obj, Control):
            self.model.controls.append(obj)
        elif isinstance(obj, Metric):
            self.model.metrics.append(obj)
        elif isinstance(obj, CompositeScore):
            self.model.composite_scores.append(obj)
        self.selected_object = obj
    
    def remove_object(self, obj):
        """ Remove an object from the current model.
        """
        if isinstance(obj, Control):
            self.model.controls.remove(obj)
            for metric in self.model.metrics:
                if obj in metric.control_for:
                    metric.control_for.remove(obj)
        elif isinstance(obj, Metric):
            self.model.metrics.remove(obj)
        elif isinstance(obj, CompositeScore):
            self.model.composite_scores.remove(obj)
