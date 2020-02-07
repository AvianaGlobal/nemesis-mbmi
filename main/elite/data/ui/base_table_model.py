from abc import abstractmethod

import numpy as np
from enaml.colors import Color
from enaml.icon import Icon
from enaml.qt.QtCore import Qt, QAbstractTableModel
from enaml.qt.q_resource_helpers import get_cached_qcolor, get_cached_qicon
from traitsui.qt4.clipboard import PyMimeData


class BaseTableModel(QAbstractTableModel):
    """ A generic Qt table model that provides sensible defaults and helper
    functions.
    """

    def __init__(self, selection_mode='none', selection_drag=False,
                 decoration=lambda i, j, v: None, *args, **kwargs):
        super(BaseTableModel, self).__init__(*args, **kwargs)
        self.selection_mode = selection_mode
        self.selection_drag = selection_drag
        self.decoration = decoration

    # BaseTableModel abstract interface

    @abstractmethod
    def get_value(self, i, j):
        raise NotImplementedError()

    @abstractmethod
    def reset_columns(self):
        raise NotImplementedError()

    @abstractmethod
    def set_columns(self, columns):
        raise NotImplementedError()

    @abstractmethod
    def can_add_column(self, column):
        raise NotImplementedError()

    @abstractmethod
    def map_to_row(self, i):
        raise NotImplementedError()

    @abstractmethod
    def map_from_row(self, row):
        raise NotImplementedError()

    # BaseTableModel interface

    def filter(self, text):
        pass

    def add_columns(self, columns):
        self.set_columns(self.get_columns() + columns)

    def remove_column(self, i):
        columns = self.get_columns()
        del columns[i]
        self.set_columns(columns)

    def remove_all_columns(self):
        for i in range(self.columnCount()):
            self.remove_column(0)

    def map_to_col(self, j):
        return self.get_columns()[j]

    def map_from_col(self, col):
        return self.get_columns().index(col)

    # Helper functions

    def format_value(self, value):
        """ Return a nice unicode formatting of the given value.
        """
        if isinstance(value, (float, np.floating)):
            if np.isnan(value):
                return u'NaN'
            if int(value) == value:
                return unicode(int(value))
            return u'%.3f' % value
        return unicode(value)

    def get_columns(self):
        return [self.headerData(i, Qt.Horizontal, Qt.DisplayRole)
                for i in range(self.columnCount())]

    def emit_all_data_changed(self):
        """ Emit signals to note that all data has changed, e.g. by sorting.
        """
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.columnCount() - 1)
        )

        self.headerDataChanged.emit(Qt.Vertical, 0, self.rowCount() - 1)

    # QAbstractTableModel interface

    def flags(self, index):
        """ Reimplemented to allow dragging, when enabled.
        """
        flags = super(BaseTableModel, self).flags(index)
        if index.isValid() and self.selection_drag:
            flags = Qt.ItemIsDragEnabled | flags
        return flags

    def mimeTypes(self):
        """ Reimplemented to expose PyMimeData mimetypes.
        """
        return [PyMimeData.MIME_TYPE, PyMimeData.NOPICKLE_MIME_TYPE]

    def mimeData(self, indexes):
        """ Reimplemented to generate PyMimeData data for the given indices.
        """
        mode = self.selection_mode

        data = []
        if mode == 'cell':
            data = ([self.map_to_row(i.row()) for i in indexes],
                    [self.map_to_col(i.column()) for i in indexes])
        elif mode == 'row':
            data = sorted({self.map_to_row(i.row()) for i in indexes})
        elif mode == 'column':
            data = sorted({self.map_to_col(i.column()) for i in indexes})

        mime_data = PyMimeData.coerce(data)
        return mime_data

    def headerData(self, section, orientation, role):
        if role == Qt.TextAlignmentRole:
            if orientation == Qt.Horizontal:
                return int(Qt.AlignHCenter | Qt.AlignVCenter)
            return int(Qt.AlignRight | Qt.AlignVCenter)

        return None

    def data(self, index, role=Qt.DisplayRole):
        if not (index.isValid() and (0 <= index.row() < self.rowCount())):
            return None

        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        elif role == Qt.DecorationRole:
            row = self.map_to_row(index.row())
            col = self.map_to_col(index.column())
            value = self.get_value(index.row(), index.column())
            data = self.decoration(row, col, value)
            if isinstance(data, Color):
                return get_cached_qcolor(data)
            elif isinstance(data, Icon):
                return get_cached_qicon(data)
            else:
                return None
        elif role == Qt.DisplayRole:
            return self.format_value(
                self.get_value(index.row(), index.column())
            )

        return None
