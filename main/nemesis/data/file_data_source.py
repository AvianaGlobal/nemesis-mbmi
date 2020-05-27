from __future__ import absolute_import

import os.path

from nemesis.r import ast
from traits.api import HasTraits, File, Instance, List, Str

from .data_source import DataSource
from .variable import Variable


class FileDataSource(DataSource):
    """ A data source associated with a flat file.
    """

    # The path to the data file.
    path = File()

    # The supported file types, listed by extension.
    file_types = List(Str)

    # A wildcard for use in file dialogs.
    wildcard = List(Str)

    # Private interface

    _file_reader = Instance('nemesis.data.file_data_source.FileReader')

    # DataSource interface

    def ast(self):
        return self._file_reader.ast(self.path)

    def load(self, variables=None):
        return self._file_reader.read_data(
            self.path,
            columns=variables,
            limit=self.num_rows if self.limit_rows else None)

    def load_metadata(self):
        df = self._file_reader.read_data(self.path, limit=10)
        self.variables = Variable.from_data_frame(df)
        return self.variables

    # Private interface

    def _find_file_reader(self, path):
        ext = os.path.splitext(path)[1]
        for reader in file_readers:
            if (ext.lower() in reader.file_types or
                    ext.upper() in reader.file_types):
                return reader
        else:
            return None

    def _file_types_default(self):
        file_types = []
        for reader in file_readers:
            file_types.extend(reader.file_types)
        return file_types

    def _wildcard_default(self):
        fmt_str = '{} ({})'
        make_glob = lambda exts: ' '.join(['*' + ext for ext in exts])
        wildcard = [fmt_str.format('All supported files',
                                   make_glob(self.file_types))]
        for reader in file_readers:
            wildcard.append(fmt_str.format(reader.name,
                                           make_glob(reader.file_types)))
        return wildcard

    # Trait change handlers

    def _path_changed(self, path):
        reader = self._find_file_reader(path)
        self.can_load = os.path.isfile(path) and reader is not None
        self._file_reader = reader


class FileReader(HasTraits):
    # The name of the file format.
    name = Str

    # The file types supported by the reader, specified as a list of extensions,
    # e.g., ['.xls', '.xlsx'].
    file_types = List(Str)

    def ast(self, path):
        """ Read data from the file, returning a data.frame.
        """
        raise NotImplementedError

    def read_data(self, path, columns=None, limit=None):
        """ Read data from the file, returning a pandas.DataFrame.
        """
        raise NotImplementedError


class CsvFileReader(FileReader):
    name = 'Comma-separated'
    file_types = ['.csv']

    def ast(self, path):
        return ast.Constant(path)

    def read_data(self, path, columns=None, limit=None):
        from pandas import read_csv
        return read_csv(path, usecols=columns, nrows=limit)


class TsvFileReader(FileReader):
    name = 'Tab-separated'
    file_types = ['.tsv', '.tab']

    def ast(self, path):
        return ast.Constant(path)

    def read_data(self, path, columns=None, limit=None):
        from pandas import read_table
        return read_table(path, usecols=columns, nrows=limit)


class ExcelFileReader(FileReader):
    name = 'Excel spreadsheet'
    file_types = ['.xls', '.xlsx']

    def ast(self, path):
        return ast.Call(ast.Name('read.xlsx'),
                        ast.Constant(path),
                        ast.Constant(1),  # Sheet index
                        libraries=['xlsx'])

    def read_data(self, path, columns=None, limit=None):
        # XXX: read_excel does not support limiting the rows or the columns.
        from pandas import read_excel
        df = read_excel(path)
        if columns is not None:
            df = df[columns]
        if limit is not None:
            df = df[:limit]
        return df


file_readers = [
    CsvFileReader(),
    TsvFileReader(),
    ExcelFileReader(),
]
