from __future__ import absolute_import

from enaml.qt.QtCore import Qt
from enaml.qt.QtGui import QTableView, QAction

from .data_frame_table import DataFrameTable


FROZEN_STYLE = """
QTableView {
    border: none;
    border-right: 2px solid #999;
}
"""


class FreezeTableView(DataFrameTable):
    """ A QTableView that supports freezing columns. Adapted from:
    http://doc.qt.io/qt-5/qtwidgets-itemviews-frozencolumn-example.html
    """
    def __init__(self, *args, **kwargs):
        super(FreezeTableView, self).__init__(*args, **kwargs)
        self._frozen_columns = []
        self._frozen_positions = {}
        self.init_frozen_view()
        self.update_frozen_geometry()

    def setModel(self, model):
        super(FreezeTableView, self).setModel(model)
        if model is None:
            return

        self._frozen_columns = []
        self._frozen_view.setModel(self.model())

        if self.selectionModel():
            self._frozen_view.setSelectionModel(self.selectionModel())

        for i in range(0, self.model().columnCount()):
            self._frozen_view.setColumnHidden(i, True)

        for i in range(0, self.model().rowCount()):
            self._frozen_view.setRowHeight(i, self.rowHeight(i))

    def init_frozen_view(self):
        self._frozen_view = QTableView(self)

        self._frozen_view.setFocusPolicy(Qt.NoFocus)
        self._frozen_view.verticalHeader().hide()
        self._frozen_view.setStyleSheet(FROZEN_STYLE)
        self._frozen_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._frozen_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Synchronize vertical scroll bars between the two table views
        self._frozen_view.verticalScrollBar().valueChanged.connect(
            self.verticalScrollBar().setValue
        )
        self.verticalScrollBar().valueChanged.connect(
            self._frozen_view.verticalScrollBar().setValue
        )

        self.verticalHeader().sectionResized.connect(
            self.update_row_height
        )

        hheader = self._frozen_view.horizontalHeader()
        hheader.setContextMenuPolicy(Qt.CustomContextMenu)
        hheader.customContextMenuRequested.connect(self._on_context_menu)
        hheader.sectionResized.connect(self.frozen_section_resized)

        self.viewport().stackUnder(self._frozen_view)
        self._frozen_view.show()

    def freeze_column(self, column):
        if column not in self._frozen_columns:
            self._frozen_columns.append(column)
            self._frozen_view.setColumnHidden(column, False)
            self._frozen_view.setColumnWidth(column, self.columnWidth(column))
            self.horizontalHeader().moveSection(
                column, len(self._frozen_columns) - 1
            )
            self.update_frozen_geometry()

            self._frozen_positions[len(self._frozen_columns) - 1] = column

    def unfreeze_column(self, column):
        if column in self._frozen_columns:
            self._frozen_columns.remove(column)
            self._frozen_view.setColumnHidden(column, True)
            self.setColumnHidden(column, False)
            self.update_frozen_geometry()

            # Move the column back to its position before it was frozen
            hheader = self.horizontalHeader()
            v = hheader.visualIndex(column)
            hheader.moveSection(v, self._frozen_positions[v])
            del self._frozen_positions[v]

            # Force a redraw, since some artifacts were being left behind
            self.update()

    def frozen_width(self):
        return sum(
            [self.columnWidth(i) for i in self._frozen_columns]
        )

    def update_frozen_geometry(self):
        self._frozen_view.setGeometry(
            self.verticalHeader().width() + self.frameWidth(),
            self.frameWidth(), self.frozen_width(),
            self.viewport().height() + self.horizontalHeader().height()
        )

    def update_row_height(self, index, old_size, size):
        self._frozen_view.setRowHeight(index, size)

    def frozen_section_resized(self, index, old_size, size):
        if index in self._frozen_columns:
            self.setColumnWidth(index, size)
            self.update_frozen_geometry()

    def resizeEvent(self, event):
        super(FreezeTableView, self).resizeEvent(event)
        self.update_frozen_geometry()

    def moveCursor(self, action, modifiers):
        current = super(FreezeTableView, self).moveCursor(action, modifiers)

        corner_x = self.visualRect(current).topLeft().x()
        if (action == QTableView.MoveLeft and current.column() > 0 and
                 corner_x < self.frozen_width()):
            value = self.horizontalScrollBar().value() + corner_x - self.frozen_width()
            self.horizontalScrollBar().setValue(value)

        return current

    def context_menu(self, col):
        menu = super(FreezeTableView, self).context_menu(col)

        if col in self._frozen_columns:
            action = QAction('Unfreeze Column', menu)
            action.setData(col)
            action.triggered.connect(self._on_unfreeze_column)

        else:
            action = QAction('Freeze Column', menu)
            action.setData(col)
            action.triggered.connect(self._on_freeze_column)

        menu.addAction(action)
        return menu

    def _on_freeze_column(self):
        col = self.sender().data()
        self.freeze_column(col)

    def _on_unfreeze_column(self):
        col = self.sender().data()
        self.unfreeze_column(col)
