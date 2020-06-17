import numpy as np

from enaml.qt.QtCore import QModelIndex, Qt

from nemesis.data.data_frame_query import DataFrameQuery
from nemesis.data.ui.base_table_model import BaseTableModel


class DataFrameTableModel(BaseTableModel):
    """ A table model for a pandas DataFrame.
    """
    
    def __init__(self, data_frame, id_column=None, *args, **kwds):
        super(DataFrameTableModel, self).__init__(*args, **kwds)
        data_frame = self._strip_index(data_frame)
        self.original_data_frame = data_frame

        if id_column is not None:
            self.id_column = id_column
        elif len(data_frame.columns) > 0:
            self.id_column = data_frame.columns[0]
        else:
            self.id_column = None

        self._sorted_column = None
        self._sorted_order = None
        self.columns = data_frame.columns
        self.set_data_frame(data_frame)

    # BaseTableModel interface

    def filter(self, text):
        df = DataFrameQuery.execute(self.original_data_frame, text)
        if df is not None:
            self.set_data_frame(df)
        else:
            self.set_data_frame(self.original_data_frame)

    def set_columns(self, columns):
        if self.id_column not in columns:
            columns.insert(0, self.id_column)

        self.columns = columns
        self.argsort_indices = None
        self.inverse_argsort_indices = None
        self.cache = ColumnCache(self.data_frame.ix[:, columns])

        if self._sorted_column in self.columns and self._sorted_order is not None:
            self.sort(self.columns.index(self._sorted_column),
                      self._sorted_order)

        self.emit_all_data_changed()

    def reset_columns(self):
        self.set_columns(self.original_data_frame.columns)
        self.emit_all_data_changed()

    def can_add_column(self, column):
        return column in self.original_data_frame.columns

    def map_to_row(self, i):
        return self.original_data_frame[self.id_column].iloc[
            self.map_view_to_data(i)
        ]

    def map_from_row(self, row):
        return self.map_data_to_view(
            self.original_data_frame[self.id_column].get_loc(row)
        )

    def map_view_to_data(self, i):
        if self.argsort_indices is not None:
            i = self.argsort_indices[i]
        return i

    def map_data_to_view(self, i):
        if self.argsort_indices is not None:
            i = self.inverse_argsort_indices[i]
        return i

    def get_value(self, i, j):
        return self.cache[self.map_view_to_data(i), j]

    # DataFrameModel interface

    def set_data_frame(self, df):
        self.data_frame = df
        self.set_columns(self.columns)

    def _strip_index(self, df):
        name = df.index.name
        columns = list(df.columns)
        if name:
            df = df.reset_index()
            columns.insert(0, name)
            df.columns = columns
        return df

    # QAbstractTableModel interface

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return unicode(self.columns[section])
        return super(DataFrameTableModel, self).headerData(section, orientation, role)

    def columnCount(self, index=QModelIndex()):
        if not index.isValid():
            return len(self.columns)
        return 0

    def rowCount(self, index=QModelIndex()):
        if not index.isValid():
            return len(self.data_frame)
        return 0

    def sort(self, column, order=Qt.AscendingOrder):
        self._sorted_column = self.columns[column]
        self._sorted_order = order
        if column == -1:
            # Return to unsorted.
            if self.argsort_indices is not None:
                self.argsort_indices = None
                self.emit_all_data_changed()
            return
        ascending = (order == Qt.AscendingOrder)
        data = self.cache.columns[column]
        # If things are currently sorted, we will try to be stable
        # relative to that order, not the original data's order.
        if self.argsort_indices is not None:
            data = data[self.argsort_indices]
        if ascending:
            indices = np.argsort(data, kind='mergesort')
        else:
            # Do the double-reversing to maintain stability.
            indices = (len(data) - 1 -
                       np.argsort(data[::-1], kind='mergesort')[::-1])
            if np.issubdtype(data.dtype, np.dtype(np.floating)):
                # The block of NaNs is now at the beginning. Move it to
                # the bottom.
                num_nans = np.isnan(data).sum()
                if num_nans > 0:
                    indices = np.roll(indices, -num_nans)
        if self.argsort_indices is not None:
            indices = self.argsort_indices[indices]
        self.argsort_indices = indices
        self.inverse_argsort_indices = np.argsort(indices)
        self.emit_all_data_changed()


class ColumnCache(object):
    """ Pull out a view for each column for quick element access.
    """

    def __init__(self, data_frame):
        self.reset(data_frame)

    def __getitem__(self, ij):
        i, j = ij
        return self.columns[j][i]

    def reset(self, new_data_frame=None):
        """ Reset the cache.
        """
        if new_data_frame is not None:
            self.data_frame = new_data_frame
        ncols = len(self.data_frame.columns)
        self.columns = [None] * ncols
        for data_block in self.data_frame._data.blocks:
            for i, ref_loc in enumerate(data_block.mgr_locs):
                self.columns[ref_loc] = data_block.values[i, :]

    def clear(self):
        """ Clear out the cache entirely.
        """
        del self.data_frame
        del self.columns
