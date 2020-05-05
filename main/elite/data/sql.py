""" Generic functions for interacting with SQL databases.
"""
from __future__ import absolute_import
import numpy as np
import pandas
import sqlalchemy


def read_sql_table(engine, table_name, index_col=None, columns=None,
                   select_from=None, limit=None, order_by=None, where=None,
                   coerce_types=None, raise_on_missing=True):
    """ Load a table from a SQL database.
    
    Parameters
    ----------
    engine : SQLAlchemy engine
        The SQL database to load from.
    
    table_name : str
        The name of the table to load.
    
    index_col : str, optional
        Column name to use as index for the returned data frame.
    
    columns : sequence of str, optional
        Columns to select from the table. By default, all columns are selected.

    select_from : str or SQLAlchemy clause, optional
        A FROM clause to use for the select statement. Defaults to the
        table name.
    
    limit : int, optional
        Limit the number of rows selected.
    
    order_by : str or SQLAlchemy clause, optional
        An ORDER BY clause to sort the selected rows.
    
    where : str or SQLAlchemy clause, optional
        A WHERE clause used to filter the selected rows.
    
    coerce_types : dict(str : dtype or Python type), optional
        Override pandas type inference for specific columns.
    
    Returns
    -------
    A pandas DataFrame.
    """
    # Pandas does not expose many of these options, so we pull out some of
    # Pandas' internals.
    #
    # An alternative approach would be to use `pandas.read_sql_query` with an
    # appropriate (dialect-specific) query. However, this approach would not 
    # utilize Pandas' logic for column type inference (performed by 
    # `_harmonize_columns()` below), and would hence produce inferior results.
    
    from sqlalchemy.schema import MetaData
    from pandas.io.sql import SQLDatabase, SQLTable

    # From pandas.io.sql.read_sql_table
    # and  pandas.io.sql.SQLDatabase.read_table:
    meta = MetaData(engine)
    try:
        meta.reflect(only=[table_name])
    except sqlalchemy.exc.InvalidRequestError:
        if raise_on_missing:
            raise ValueError("Table %s not found" % table_name)
        else:
            return None

    pd_db = SQLDatabase(engine, meta=meta)
    pd_tbl = SQLTable(table_name, pd_db, index=None)

    # table, query = SQLDataSource.table, SQLDataSource.query
    #
    # if SQLDataSource.dialect == 'mssql':
    #     import pyodbc
    #     SERVER = SQLDataSource.host
    #     DATABASE = SQLDataSource.database
    #     UID = SQLDataSource.username
    #     PWD = SQLDataSource.password
    #
    #     path = 'DRIVER={ODBC Driver 17 for SQL Server}; SERVER=' + str(SERVER) + ';DATABASE=' + str(
    #         DATABASE) + ';Trusted_Connection=yes;UID=' + str(UID) + ';PWD=' + str(PWD)
    #     conn = pyodbc.connect(path)
    #
    #     if table != 'NA':
    #         query = "select * from " + str(table)
    #     else:
    #         query = self.query
    #
    #     # use read_sql_table
    #     pd_tbl = pd.read_sql(query, conn)

    
    # Adapted from pandas.io.SQLTable.read:
    if columns is not None and len(columns) > 0:
        if index_col is not None and index_col not in columns:
            columns = [index_col] + columns
        
        cols = [pd_tbl.table.c[n] for n in columns]
    else:
        cols = pd_tbl.table.c

    if pd_tbl.index is not None:
        [cols.insert(0, pd_tbl.table.c[idx]) for idx in pd_tbl.index[::-1]]

    # Strip the table name from each of the column names to allow for more
    # general FROM clauses.
    sql_select = sqlalchemy.select([
        sqlalchemy.column(str(c).replace('{}.'.format(table_name), '', 1))
        for c in cols
    ])

    if select_from is not None:
        sql_select = sql_select.select_from(select_from)
    else:
        sql_select = sql_select.select_from(
            sqlalchemy.table(table_name)
        )

    if where is not None:
        if isinstance(where, basestring):
            where = sqlalchemy.text(where)
        sql_select = sql_select.where(where)
    if limit is not None:
        sql_select = sql_select.limit(limit)
    if order_by is not None:
        if isinstance(order_by, basestring):
            order_by = sqlalchemy.sql.column(order_by)
        sql_select = sql_select.order_by(order_by)
    
    result = pd_db.execute(sql_select)
    data = result.fetchall()
    column_names = result.keys()

    pd_tbl.frame = pandas.DataFrame.from_records(data, index=index_col,
                                             columns=column_names)

    # This line has caused issues with incorrect type inference -- add it
    # back with caution.
    # pd_tbl._harmonize_columns()
    
    # Added by me: coerce types
    if coerce_types:
        frame = pd_tbl.frame
        for col, dtype in coerce_types.iteritems():
            frame[col] = frame[col].astype(dtype, copy=False)
    
    return pd_tbl.frame


def sample_sql_table(engine, table_name, n, where=None, **kw):
    """ Sample rows randomly from a SQL table.
    
    Parameters
    ----------
    engine : SQLAlchemy engine
    table_name : str
        Same as  ``load_sql_table``.
    
    n : int
        The number of samples. If greater than the number of rows in the table,
        the whole table is returned.

    where : str or SQLAlchemy clause, optional
        A WHERE clause used to sample a subset of rows.
    
    **kw : dict
        Additional arguments to pass to ``read_sql_table``.

    Returns
    -------
    A pandas DataFrame.
    """
    # Naive, dialect-agnostic queries for random sampling are very slow
    # (linear or log-linear in total number of rows).
    #
    # Some references:
    #   http://stackoverflow.com/questions/2279706
    #   https://www.periscope.io/blog/how-to-sample-rows-in-sql-273x-faster.html
    #   http://www.titov.net/2005/09/21/do-not-use-order-by-rand-or-how-to-get-random-rows-from-table/
    table = sqlalchemy.table(table_name)

    count_select = sqlalchemy.select([sqlalchemy.func.count()])
    if where is not None:
        count_select = count_select.where(where)

    count = engine.execute(count_select.select_from(table)).fetchone()[0]

    order_by = None
    sample_where = None
    select_from = None

    if n < count:
        order_by = sqlalchemy.sql.func.random()
        k = count / float(n)
        sample_where = sqlalchemy.sql.func.random() % k == 0

        if where is not None:
            select_from = (sqlalchemy.select('*')
                .select_from(table)
                .where(where))

    return read_sql_table(engine, table_name, select_from=select_from,
                          where=sample_where, order_by=order_by, limit=n, **kw)
