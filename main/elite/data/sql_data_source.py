from __future__ import absolute_import

import os.path

import sqlalchemy
from elite.r import ast
from traits.api import Bool, Enum, Int, Property, Str

from .data_source import DataSource
# from .sql import read_sql_table, sample_sql_table
from .variable import Variable
import pandas as pd


def read_sql_table(engine, dialect, table_name=None, host=None, port=None, database=None, username=None, password=None,
                   query=None, limit=None, index_col=None, columns=None, select_from=None, order_by=None, where=None,
                   coerce_types=None, raise_on_missing=True):

    global pd_tbl

    if table_name != 'NA':
        query = "select * from " + str(table_name)

    if dialect == 'mssql':
        import pyodbc

        SERVER = host
        DATABASE = database
        UID = username
        PWD = password

        path = 'DRIVER={ODBC Driver 17 for SQL Server}; SERVER=' + str(SERVER) + ',' + str(port) + ';DATABASE=' + str(
            DATABASE) + ';Trusted_Connection=yes;UID=' + str(UID) + ';PWD=' + str(PWD)

        conn = pyodbc.connect(path)
        pd_tbl = pd.read_sql(query, conn)

    if dialect == "sqlite":
        import sqlite3

        conn = sqlite3.connect(database)
        pd_tbl = pd.read_sql_query(query, conn)

    if dialect == "db2":
        import ibm_db
        import ibm_db_dbi

        DATABASE = database
        HOSTNAME = host
        PORT = 50000
        UID = username
        PWD = password

        path = 'DATABASE=' + str(DATABASE) + ';HOSTNAME=' + str(HOSTNAME) + ';PORT=' + str(
            PORT) + ';PROTOCOL=TCPIP' + ';UID=' + str(UID) + ';PWD=' + str(PWD)

        connection = ibm_db.connect(path, '', '')
        conn = ibm_db_dbi.Connection(connection)

        pd_tbl = pd.read_sql_query(query, conn)

    if limit is not None:
        pd_tbl = pd_tbl[0:limit]


    # from sqlalchemy.schema import MetaData
    # from pandas.io.sql import SQLDatabase, SQLTable

    # From pandas.io.sql.read_sql_table
    # and  pandas.io.sql.SQLDatabase.read_table:
    # meta = MetaData(engine)
    # try:
    #     meta.reflect(only=[table_name])
    # except sqlalchemy.exc.InvalidRequestError:
    #     if raise_on_missing:
    #         raise ValueError("Table %s not found" % table_name)
    #     else:
    #         return None

    # pd_db = SQLDatabase(engine, meta=meta)
    # pd_tbl = SQLTable(table_name, pd_db, index=None)

    # Adapted from pandas.io.SQLTable.read:
    # if columns is not None and len(columns) > 0:
    #     if index_col is not None and index_col not in columns:
    #         columns = [index_col] + columns
    #
    #     cols = [pd_tbl.table.c[n] for n in columns]
    # else:
    # cols = list(pd_tbl.columns)

    # if pd_tbl.index is not None:
    #     [cols.insert(0, pd_tbl.table.c[idx]) for idx in pd_tbl.index[::-1]]

    # Strip the table name from each of the column names to allow for more
    # general FROM clauses.
    # sql_select = sqlalchemy.select([
    #     sqlalchemy.column(str(c).replace('{}.'.format(table_name), '', 1))
    #     for c in cols
    # ])
    #
    # if select_from is not None:
    #     sql_select = sql_select.select_from(select_from)
    # else:
    #     sql_select = sql_select.select_from(
    #         sqlalchemy.table(table_name)
    #     )
    #
    # if where is not None:
    #     if isinstance(where, basestring):
    #         where = sqlalchemy.text(where)
    #     sql_select = sql_select.where(where)
    # if limit is not None:
    #     sql_select = sql_select.limit(limit)
    # if order_by is not None:
    #     if isinstance(order_by, basestring):
    #         order_by = sqlalchemy.sql.column(order_by)
    #     sql_select = sql_select.order_by(order_by)

    # result = pd_db.execute(sql_select)
    # data = result.fetchall()
    # column_names = result.keys()
    #
    # pd_tbl.frame = pd.DataFrame.from_records(data, index=index_col,
    #                                              columns=column_names)
    #
    # # This line has caused issues with incorrect type inference -- add it
    # # back with caution.
    # # pd_tbl._harmonize_columns()
    #
    # # Added by me: coerce types
    # if coerce_types:
    #     frame = pd_tbl.frame
    #     for col, dtype in coerce_types.iteritems():
    #         frame[col] = frame[col].astype(dtype, copy=False)

    return pd_tbl



class SQLDataSource(DataSource):
    """ A data source associated with a SQL database.
    """
    # The type of database.
    dialect = Enum('db2', 'mssql', 'sqlite')
    # Connection information.
    host = Str('AVIANATEMP1218')
    port = Int(50000)
    username = Str('sa')
    password = Str('Password123$')
    # The database and table to load from.
    # Note: When using sqlite, `database` is the filename.
    database = Str('demodb')
    table = Str('Alphabet')
    query = Str('')
    conn = Str('odbc()')
    driver = Str('IBM DB2 ODBC DRIVER - DB2COPY1')
    dsn = Str('Nemesis SQL odbc')
    db2dsn = Str("Driver={IBM DB2 ODBC DRIVER};"
                 "DATABASE=BLUDB;"
                 "HOSTNAME=dashdb-txn-sbox-yp-dal09-03.services.dal.bluemix.net;"
                 "PORT=50000;"
                 "PROTOCOL=TCPIP;"
                 "UID=xjv23492;"
                 "PWD=fhg^61d4pw6114j3;")

    msconn = Str("DRIVER={SQL Server Native Client 11.0};" 
                 "SERVER=AVIANATEMP1218;"
                 "DATABASE=demodb;"
                 "UID=sa;"
                 "PWD=Password123$;")

    def get_mssql_connection_str(self):
        return 'DRIVER={ODBC Driver 17 for SQL Server}; SERVER='+str(self.host)+';DATABASE='+str(self.database)+';UID='+str(self.username)+';PWD='+str(self.password)

    def get_ibmdb2_connection_str(self):
        return

    def create_query(self):
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
            return [(ast.Name('ConnStr'), ast.Constant(self.get_mssql_connection_str())),
                    (ast.Name('input_table'), ast.Constant(self.create_query())),
                    (ast.Name('MSSQL'), ast.Constant(1))]

        elif self.dialect == 'sqlite':
            return [(ast.Name('sqlitepath'), ast.Constant(self.database)),
                    (ast.Name('input_table'), ast.Constant(self.create_query())),
                    (ast.Name('Sqlite'), ast.Constant(1))]

        # still need to fix IBM DB2 R connection
        else:
            return [(ast.Name('input'), conn),
                    (ast.Name('input_table'), ast.Constant(self.table)),
                    (ast.Name('MSSQL'), ast.Constant(0)),
                    (ast.Name('Sqlite'), ast.Constant(0))]

    def load(self, variables=None):
        return self.load_table(self.dialect, self.table, self.host, self.port, self.database, self.username,
                               self.password, self.query, columns=variables,
                               limit=self.num_rows if self.limit_rows else None)

    def load_metadata(self):
        # Use pandas type inference, rather than trying it ourselves
        # based on DB's column type.
        df = self.load_table(self.dialect, self.table, self.host, self.port, self.database, self.username, self.password, self.query, limit=10)
        self.variables = Variable.from_data_frame(df)
        return self.variables
    # SQLDataSource interface

    def ast_for_dbi_call(self, call_name, *call_args):
        """ Returns a Call to an R function supporting the DBI connections parameters.
        """
        if self.dialect == 'db2':
            args = [
                (ast.Name(self.conn)),
                (ast.Name('.connection_string'), ast.Constant(self.db2dsn)),
                # (ast.Name('dsn'), ast.Constant(self.dsn)),
                # (ast.Name('driver'), ast.Constant(self.driver)),
            ]
        else:
            args = [ast.Call(ast.Name('dbDriver'), ast.Constant(R_DBI_DRIVERS[self.dialect]))]
        args += call_args
        args += [(ast.Name('dbname'), ast.Constant(self.database))]

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


    def load_table(self, dialect, table=None, host=None, port=None, database=None, username=None, password=None, query=None, **kw):
        """ Load a table from the database.
        """
        engine = self.create_engine()
        return read_sql_table(engine, dialect, table, host, port, database, username, password, query, **kw)

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
    'mssql': 1433,
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
