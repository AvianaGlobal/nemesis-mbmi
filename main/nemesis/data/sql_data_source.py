from __future__ import absolute_import

import os.path
import pandas as pd
import sqlalchemy
from nemesis.r import ast
from traits.api import Bool, Enum, Int, Property, Str

from .data_source import DataSource
from .sql import read_sql_table, sample_sql_table
from .variable import Variable
from .file_data_source import FileDataSource, FileReader, CsvFileReader

class SQLDataSource(DataSource):
    """ A data source associated with a SQL database.
    """
    # The type of database.
    dialect = Enum('db2', 'mssql', 'sqlite')
    # Connection information.
    host = Str()
    port = Int()
    username = Str()
    password = Str()
    # The database and table to load from.
    # Note: When using sqlite, `database` is the filename.
    database = Str()
    table = Str()
    query = Str()
    conn = Str('odbc()')
    driver = Str('IBM DB2 ODBC DRIVER')
    dsn = Str()
    db2dsn = Str("Driver={IBM DB2 ODBC DRIVER};"
                 "DATABASE=BLUDB;"
                 "HOSTNAME=dashdb-txn-sbox-yp-dal09-03.services.dal.bluemix.net;"
                 "PORT=50000;"
                 "PROTOCOL=TCPIP;"
                 "UID=xjv23492;"
                 "PWD=fhg^61d4pw6114j3;")

    def sql_connection_str(self):
        return 'DRIVER={ODBC Driver 17 for SQL Server}; SERVER='+str(self.host)+';DATABASE='+str(self.database)+\
               ';UID='+str(self.username)+';PWD='+str(self.password)

    def DB2_connection_str(self):
        return 'DRIVER={IBM DB2 ODBC DRIVER}; DATABASE='+str(self.database)+';HOSTNAME='+str(self.host)+';PORT='+\
               str(self.port)+';PROTOCOL=TCPIP;UID='+str(self.username)+';PWD='+str(self.password)

    def query_table(self):
        if self.table != 'NA':
            return "select * from " + str(self.table)
        else:
            return self.query

    # Whether there is enough information to connect to the database.
    can_connect = Property(Bool, depends_on=['dialect', 'host', 'username', 'password', 'database'])
    # DataSource interface
    can_load = Property(Bool, depends_on=['can_connect', 'table'])

    def ast(self):
        conn = self.ast_for_dbi_call(ast.Name('dbConnect'))
        print('ast')
        if self.dialect == 'mssql':
            return [(ast.Name('ConnStr'), ast.Constant(self.sql_connection_str())),
                    (ast.Name('input_table'), ast.Constant(self.query_table())),
                    (ast.Name('MSSQL'), ast.Constant(1))]

        elif self.dialect == 'sqlite':
            return [(ast.Name('sqlitepath'), ast.Constant(self.database)),
                    (ast.Name('input_table'), ast.Constant(self.query_table())),
                    (ast.Name('Sqlite'), ast.Constant(1))]

        elif self.dialect == 'db2':
            return [(ast.Name('ConnStr'), ast.Constant(self.DB2_connection_str())),
                    (ast.Name('input_table'), ast.Constant(self.query_table())),
                    (ast.Name('db2'), ast.Constant(1))]
        else:
            return [(ast.Name('input'), conn),
                    (ast.Name('input_table'), ast.Constant(self.table)),
                    (ast.Name('MSSQL'), ast.Constant(0)),
                    (ast.Name('Sqlite'), ast.Constant(0)),
                    (ast.Name('db2'), ast.Constant(0))]


    def load(self, variables=None):

        # if self.table is not None and self.table != "NA":
        print('load')
        return self.load_table(
            self.table,
            columns=variables,
            limit=self.num_rows if self.limit_rows else None)

    def load_metadata(self):
        # Use pandas type inference, rather than trying it ourselves
        # based on DB's column type.
        df = self.load_table(self.table, limit=10)
        self.variables = Variable.from_data_frame(df)
        return self.variables

    # SQLDataSource interface
    def ast_for_dbi_call(self, call_name, *call_args):
        """ Returns a Call to an R function supporting the DBI connections parameters.
        """
        if self.dialect == 'db2':
            args = [
                (ast.Name(self.conn)),
                (ast.Name('.connection_string'), ast.Constant(self.DB2_connection_str())),
                # (ast.Name('dsn'), ast.Constant(self.dsn)),
                # (ast.Name('driver'), ast.Constant(self.driver)),
            ]
        else:
            args = [ast.Call(ast.Name('dbDriver'), ast.Constant(R_DBI_DRIVERS[self.dialect]))]
        args += call_args
        args += [(ast.Name('dbname'), ast.Constant(self.database))]
        # if self.dialect != 'sqlite':
        #     args += [(ast.Name('user'), ast.Constant(self.username)),
        #              (ast.Name('password'), ast.Constant(self.password)),
        #              (ast.Name('host'), ast.Constant(self.host)), ]
        return ast.Call(call_name, args, libraries=['DBI', R_DBI_LIBRARIES[self.dialect]])

    def create_engine(self):
        """ Create a SQLAlchemy engine for interacting with the database.
        """
        if self.dialect == 'sqlite':
            path = os.path.abspath(self.database)
            engine_str = 'sqlite:///{path}'.format(path=path)
        elif self.dialect == 'mssql':
            engine_str = '{dialect}+pyodbc://{username}:{password}@{dsn}'.format(**self.__dict__)
        elif self.dialect == 'db2':
            engine_str = 'ibm_db_sa://{username}:{password}@{host}:{port}/{database}'.format(**self.__dict__)
        else:
            engine_str = '{dialect}://{username}:{password}@{host}:{port}/{database}'.format(**self.__dict__)
        return sqlalchemy.create_engine(engine_str, echo=True)

    def load_table(self, table, **kw):
        """ Load a table from the database.
        """
        engine = self.create_engine()
        if self.table == "NA":

            query = self.query
            conn = engine.connect()
            data = pd.read_sql(query, conn)
            data.to_sql('Nemesis_data', conn, if_exists='replace', index=False)
            table = 'Nemesis_data'
            return read_sql_table(engine, table, **kw)

        else:
            print('loadtable')
            return read_sql_table(engine, table, **kw)


    def sample_table(self, table, n, **kw):
        """ Randomly sample from a table in the database.
        """
        engine = self.create_engine()
        return sample_sql_table(engine, table, n, **kw)

    # Private interface
    def _get_can_connect(self):
        ok = bool(self.database)
        if self.dialect != 'sqlite':
            ok = ok and bool(self.host and self.username and self.password)
        return ok

    def _get_can_load(self):
        return bool(self.can_connect and self.table)

    def _dialect_changed(self):
        self.port = self._port_default()

    def _port_default(self):
        return DEFAULT_PORT_MAP[self.dialect]


# Default port numbers for database dialects.
# Reference: http://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
DEFAULT_PORT_MAP = {
    'db2': 50000,
    'mssql': 55894,
    'sqlite': 0,  # no port
}

R_DBI_DRIVERS = {
    'db2': '{IBM DB2 ODBC DRIVER - DB2COPY1}',
    'mssql': '{ODBC Driver 17 for SQL Server}',
    'sqlite': 'SQLite',
}

R_DBI_LIBRARIES = {
    'db2': 'odbc',
    'mssql': 'odbc',
    'sqlite': 'RSQLite',
}
