from math import ceil
from threading import Thread

import sqlalchemy
from enaml.qt.QtCore import Qt, QModelIndex

from nemesis.data.ui.base_table_model import BaseTableModel


class SQLLazyCache(object):
    """ A caching data source that fetches results lazily from a SQL table
    """
    def __init__(self, engine, table, columns, id_column, chunk_size=100,
                 prefetch=1):
        """ Initialize the cache.

        Parameters:
        -----------
        engine : SQLAlchemy engine
            The engine that is connected to the SQL database

        table : str
            The name of the table to fetch data from

        columns : list
            A list of column names to include from the table

        id_column : str
            The name of the column that uniquely identifies each row.

        chunk_size : int, optional
            The number of rows to fetch per chunk from the database

        prefetch : int, optional
            The number of chunks to fetch before and after the current chunk.
        """
        self.engine = engine
        self.table = table
        self.columns = columns
        self.id_column = id_column
        self.chunk_size = chunk_size
        self.prefetch = prefetch
        self.sorted = None
        self.where = None

        self.reset()

    def reset(self):
        """ Reset the cache.
        """
        try:
            next_rows = self._compute_row_count()
        except:
            return

        self.total_rows = next_rows
        self._cache = {}
        self._row_to_idx = {}

    def __getitem__(self, item):
        """ Fetch an item from the cache.
        """
        i, j = item

        if i >= self.total_rows:
            raise IndexError('Invalid row index')

        chunk = i / self.chunk_size

        thread = Thread(target=self.prefetch_chunks, args=(chunk,))
        thread.start()
        self.fetch_chunk(chunk)
        thread.join()

        return self._cache[chunk][i % self.chunk_size][j]

    def prefetch_chunks(self, chunk):
        """ Prefetch chunks before and after a given chunk.
        """
        for k in range(chunk - self.prefetch, chunk):
            self.fetch_chunk(k)

        for k in range(chunk - 1, chunk + self.prefetch + 1):
            self.fetch_chunk(k)

    def sort(self, column, ascending):
        """ Sort the data by a column.

        Parameters
        ----------
        column : int
            The index of the column to sort by

        ascending : bool
            Whether the sort is ascending (True) or descending (False)

        """
        self.sorted = (column, ascending)
        self.reset()

    def filter(self, text):
        """ Filter the data with a where clause.

        Parameters
        ----------
        text : str
            The clause to filter by
        """
        self.where = text
        self.reset()

    def map_to_row(self, i):
        """ Map an integer row position to a row identifier.
        """
        return self[i, self.columns.index(self.id_column)]

    def map_from_row(self, row):
        """ Map a row identifier to an integer row position.
        """
        if row in self._row_to_idx:
            return self._row_to_idx[row]

        # This is a brute force fallback, but there is no easy database
        # agnostic way to get row indices in a query.
        total_chunks = int(ceil(self.total_rows / float(self.chunk_size)))
        for chunk in range(0, total_chunks):
            self.fetch_chunk(chunk)
            if row in self._row_to_idx:
                return self._row_to_idx[row]

        return None

    def fetch_chunk(self, chunk, force=False):
        """ Fetch a chunk from the database.

        Parameters
        ----------
        chunk : int
            The index of the chunk to fetch.

        force : bool, optional
            Refetch the chunk even if it is already in the cache.

        """
        total_chunks = ceil(self.total_rows / float(self.chunk_size))

        if chunk < 0 or chunk >= total_chunks:
            return

        if chunk in self._cache and not force:
            return

        offset = chunk * self.chunk_size
        limit = self.chunk_size

        table = sqlalchemy.table(self.table)
        columns = map(sqlalchemy.column, self.columns)
        query = sqlalchemy.select(columns).select_from(table)

        if self.sorted is not None:
            col, ascending = self.sorted
            order_by = sqlalchemy.column(self.columns[col])
            if ascending:
                order_by = sqlalchemy.asc(order_by)
            else:
                order_by = sqlalchemy.desc(order_by)

            query = query.order_by(order_by)

        query = query.offset(offset).limit(limit)

        if self.where is not None and len(self.where) > 0:
            query = query.where(sqlalchemy.text(self.where))

        chunk_data = self.engine.execute(query).fetchall()
        self._cache[chunk] = chunk_data

        id_index = self.columns.index(self.id_column)
        for i, row in enumerate(chunk_data):
            self._row_to_idx[row[id_index]] = i + offset

    def _compute_row_count(self):
        table = sqlalchemy.table(self.table)
        select = sqlalchemy.select([sqlalchemy.func.count()])
        query = select.select_from(table)

        if self.where is not None and len(self.where) > 0:
            query = query.where(sqlalchemy.text(self.where))

        return self.engine.execute(query).fetchone()[0]


class SQLTableModel(BaseTableModel):
    """ A table model for SQL tables that lazily loads its data.
    """
    def __init__(self, engine, table, id_column, columns=None, *args, **kwargs):
        super(SQLTableModel, self).__init__(*args, **kwargs)
        self.engine = engine
        self.id_column = id_column
        self.original_columns = self._get_columns(engine, table, columns)
        self.cache = SQLLazyCache(engine, table, self.original_columns,
                                  self.id_column)

    # BaseTableModel interface

    def get_value(self, i, j):
        return self.cache[i, j]

    def reset_columns(self):
        self.set_columns(self.original_columns)

    def set_columns(self, columns):
        if self.id_column not in columns:
            columns.insert(0, self.id_column)
        self._set_columns(columns)

    def can_add_column(self, column):
        return column in self.original_columns

    def get_columns(self):
        return self.cache.columns[:]

    def filter(self, text):
        self.cache.filter(text)
        self.emit_all_data_changed()

    def map_to_row(self, i):
        return self.cache.map_to_row(i)

    def map_from_row(self, row):
        return self.cache.map_from_row(row)

    # QAbstractTableModel interface

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return unicode(self.cache.columns[section])

        return super(SQLTableModel, self).headerData(section, orientation, role)

    def rowCount(self, index=QModelIndex()):
        if not index.isValid():
            return self.cache.total_rows
        return 0

    def columnCount(self, index=QModelIndex()):
        if not index.isValid():
            return len(self.cache.columns)
        return 0

    def sort(self, column, order=Qt.AscendingOrder):
        self.cache.sort(column, order == Qt.AscendingOrder)
        self.emit_all_data_changed()

    # SQLTableModel interface

    def _get_columns(self, engine, table, columns):
        if columns is not None:
            return columns

        t = sqlalchemy.table(table)
        q = sqlalchemy.select('*').select_from(t)
        result = engine.execute(q)
        return [d[0] for d in result.cursor.description]

    def _set_columns(self, columns):
        self.cache.columns = columns
        self.cache.reset()
        self.emit_all_data_changed()
