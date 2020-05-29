import cPickle as pickle

from atom.api import Typed, List, Bool, Str, Event, observe
from enaml.core.api import d_
from enaml.widgets.api import Container

from nemesis.tests.ui.base_table_model import BaseTableModel


class DataExplorerBase(Container):
    # The model to display.
    model = d_(Typed(BaseTableModel))

    # The currently selected items.
    selected = d_(List())
    multiselect = d_(Bool(False))
    selection_drag = d_(Bool(False))
    selection_mode = d_(Str('none'))

    # Filter field text
    filter_text = d_(Str())

    # An event fired when a data explorer widget is changed
    dirtied = d_(Event())

    @observe('model', 'columns')
    def _on_dirtied(self, change):
        # Don't consider the initial loading of data as a change
        if change['type'] == 'update' and change['oldvalue'] is not None:
            self.dirtied = True

    @observe('filter_text')
    def _change_filter_text(self, change):
        if self.model:
            self.model.filter(change['value'])

    def save_state(self):
        return {
            'selected': pickle.dumps(self.selected),
            # 'search_text': self.search_text,
            'filter_text': self.filter_text
        }

    def restore_state(self, state):
        selected = state.get('selected')
        if selected is not None:
            self.selected = pickle.loads(str(state['selected']))

        self.filter_text = state.get('filter_text', self.filter_text)
