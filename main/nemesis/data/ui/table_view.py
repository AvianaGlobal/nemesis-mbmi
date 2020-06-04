import sys

from enaml.qt.QtGui import *
from enaml.qt.QtCore import *
from enaml.qt.QtWidgets import *

from traitsui.qt4.clipboard import PyMimeData

from nemesis.data.variable import Variable
from nemesis.data.ui.base_table_model import BaseTableModel


MODE_MAP = {
    'cell': QAbstractItemView.SelectItems,
    'row': QAbstractItemView.SelectRows,
    'column': QAbstractItemView.SelectColumns
}


class TableView(QTableView):
    """ A generic table view with sensible defaults and context menu support.
    """
    def __init__(self, model, parent=None, editable=False,
                 on_selection=lambda: None, multiselect=False, **kwds):
        super(TableView, self).__init__(parent)

        self.editable = editable
        self.on_selection = on_selection
        self.multiselect = multiselect

        self._setup_scrolling()
        self._setup_headers()
        self._setup_style()

        if model is not None:
            self.setModel(model)

    def context_menu(self, col):
        menu = QMenu()

        if self.editable:
            remove_action = QAction("Remove Column", menu)
            remove_action.setData(col)
            remove_action.triggered.connect(self._on_remove_column)
            menu.addAction(remove_action)

        return menu

    def setModel(self, model):
        assert isinstance(model, BaseTableModel)
        super(TableView, self).setModel(model)

        self._setup_selection()
        self.selectionModel().selectionChanged.connect(self.on_selection)

        self._setup_drag_drop()
        self._setup_sorting()

    def dragEnterEvent(self, event):
        if not self.editable:
            return

        q_data = event.mimeData()
        if q_data.hasFormat(PyMimeData.MIME_TYPE):
            data = PyMimeData.coerce(q_data).instance()
            names = self._get_drop_names(data)
            if (names is not None and
                    all([self.model().can_add_column(n) for n in names])):
                event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        q_data = event.mimeData()

        if q_data.hasFormat(PyMimeData.MIME_TYPE):
            data = PyMimeData.coerce(q_data).instance()
            names = self._get_drop_names(data)
            self.model().add_columns(names)
            event.acceptProposedAction()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            text = self.selection_as_text()
            if text:
                QApplication.clipboard().setText(text)
        else:
            super(TableView, self).keyReleaseEvent(event)

    def selection_as_text(self, row_sep='\n', col_sep='\t'):
        """ Convert the current selection in the table into text.
        """
        model = self.model()
        indexes = sorted(self.selectionModel().selectedIndexes())

        if len(indexes) == 0:
            return ''

        data = [[]]
        current_row = indexes[0].row()
        for index in indexes:
            if index.row() != current_row:
                current_row = index.row()
                data.append([])

            value = model.data(index)
            data[-1].append(value)

        return row_sep.join([col_sep.join(r) for r in data])

    def _setup_sorting(self):
        # setSortingEnabled makes an initial call to sortByColumn with the
        # current sorted column and order, which defaults to the first column
        # and ascending. To prevent automatic sorting of the first column, we
        # call sortByColumn here to set the initial sorting column and order.
        self.sortByColumn(-1, Qt.DescendingOrder)
        self.setSortingEnabled(True)

    def _setup_selection(self):
        mode = self.model().selection_mode

        if mode == 'none':
            self.setSelectionMode(QAbstractItemView.NoSelection)
        else:
            self.setSelectionMode(QAbstractItemView.ExtendedSelection
                                  if self.multiselect
                                  else QAbstractItemView.SingleSelection)
            self.setSelectionBehavior(MODE_MAP[mode])

        self.setCornerButtonEnabled(False)

    def _setup_scrolling(self):
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)

    def _setup_drag_drop(self):
        self.setDragEnabled(self.model().selection_drag)
        self.setAcceptDrops(True)

    def _setup_headers(self):
        hheader = self.horizontalHeader()
        hheader.setContextMenuPolicy(Qt.CustomContextMenu)
        hheader.setStretchLastSection(False)
        hheader.setSectionsMovable(True)
        hheader.customContextMenuRequested.connect(self._on_context_menu)

        vheader = self.verticalHeader()
        # Default header has too much padding on Windows.
        if sys.platform == 'win32':
            font_metrics = vheader.fontMetrics()
            vheader.setDefaultSectionSize(font_metrics.height() + 6)
        vheader.setSectionResizeMode(QHeaderView.Fixed)
        vheader.setStretchLastSection(False)

    def _setup_style(self):
        self.setWordWrap(False)

    def _on_context_menu(self, pos):
        col = self.indexAt(pos).column()
        menu = self.context_menu(col)
        if menu and len(menu.actions()) > 0:
            menu.exec_(self.mapToGlobal(pos))

    def _on_remove_column(self):
        col = self.sender().data()
        self.model().remove_column(col)

    def _get_drop_names(self, data):
        """ Support drops from Traits UI table and tabular editors,
        where drop items can be strings or Variables.
        """
        if not isinstance(data, list):
            return None
        names = []
        for obj in data:
            if isinstance(obj, basestring):
                names.append(obj)
            elif isinstance(obj, Variable):
                names.append(obj.name)
            else:
                return None
        return names