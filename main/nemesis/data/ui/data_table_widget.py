from __future__ import absolute_import

from atom.api import Bool, Enum, List, ForwardTyped, Typed, observe, set_default
from enaml.core.declarative import d_, d_func
from enaml.widgets.api import RawWidget

from enaml.qt.QtGui import *
from enaml.qt.QtCore import *

from nemesis.data.ui.base_table_model import BaseTableModel
from nemesis.data.ui.table_view import TableView


class DataTableWidget(RawWidget):
    """ An Enaml widget that displays a table view.
    """
    # By default, Atom objects are not weak-referencable, but PySide slots
    # use weak references.
    __slots__ = '__weakref__'
    
    # The model to display.
    model = d_(Typed(BaseTableModel))
    
    # Can the user control which columns are visible?
    columns_editable = d_(Bool(False))
    
    # The currently selected items.
    selected = d_(List())
    
    # Selection settings.
    multiselect = d_(Bool(False))
    selection_drag = d_(Bool(False))
    selection_mode = d_(Enum('none', 'cell', 'row', 'column'))
    
    # Expand the table by default.
    hug_width = set_default('weak')
    hug_height = set_default('weak')
    
    # Internal storage for the table view.
    _table = ForwardTyped(lambda: TableView)
    _table_updating = Bool(False)
    _selection_updating = Bool(False)

    def create_widget(self, parent):
        """ Create the DataFrameTable Qt widget.
        """
        # XXX: This seemingly useless line triggers a change event.
        # Due to some bug in Atom and/or Enaml, the synchronization between
        # selection attributes is not set up propertly without it.
        #
        # If you remove this line, test carefully!
        self.selected = list(self.selected)

        if self.model:
            self.model.selection_mode = self.selection_mode
            self.model.selection_drag = self.selection_drag
            self.model.decoration = self.decoration
        
        self._table = TableView(
            self.model, parent, editable=self.columns_editable,
            on_selection=self._on_selected_signal, multiselect=self.multiselect
        )

        self._update_selected()
        return self._table

    @d_func
    def decoration(self, i, j, value):
        """ The decoration for the given cell.
        
        The returned value should be an enaml Color or Icon or None.
        """
        return None

    def set_model(self, model):
        if model and self._table:
            model.selection_mode = self.selection_mode
            model.selection_drag = self.selection_drag
            model.decoration = self.decoration
            self._table.setModel(model)

    # Atom change handlers

    @observe('model')
    def _update_model(self, change):
        if change['type'] == 'update':
            self.set_model(change['value'])
    
    @observe('selected')
    def _update_selected(self, change=None):
        mode = self.selection_mode
        if mode == 'none' or self._selection_updating or not self._table:
            return
        
        self._selection_updating = True
        try:
            model = self._table.model()
            selection_model = self._table.selectionModel()

            if model is None or selection_model is None:
                return

            selection_model.clearSelection()
            flags = QItemSelectionModel.Select
            if mode == 'cell':
                indexes = [model.createIndex(model.map_from_row(r),
                                             model.map_from_col(c))
                           for r, c in self.selected]
            elif mode == 'row':
                flags |= QItemSelectionModel.Rows
                indexes = [model.createIndex(model.map_from_row(r), 0)
                           for r in self.selected]
            elif mode == 'column':
                flags |= QItemSelectionModel.Columns
                indexes = [model.createIndex(0, model.map_from_col(c))
                           for c in self.selected]
            for index in indexes:
                selection_model.select(index, flags)
        finally:
            self._selection_updating = False
    
    # Qt signal handlers
    
    def _on_selected_signal(self):
        if self._selection_updating:
            return
        self._selection_updating = True
        try:
            model = self._table.model()
            mode = self.selection_mode

            selected = []
            selection_model = self._table.selectionModel()
            if mode == 'cell':
                indexes = selection_model.selectedIndexes()
                selected = [(model.map_to_row(i.row()),
                             model.map_to_col(i.column())) for i in indexes]
            elif mode == 'row':
                indexes = selection_model.selectedRows()
                selected = [model.map_to_row(i.row()) for i in indexes]
            elif mode == 'column':
                indexes = selection_model.selectedColumns()
                selected = [model.map_to_col(i.column()) for i in indexes]
            self.selected = selected
        finally:
            self._selection_updating = False