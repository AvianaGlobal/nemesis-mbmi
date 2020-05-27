from __future__ import absolute_import

from pandasql import sqldf


class DataFrameQuery(object):
    """ An SQL query that can be evaluated on a DataFrame.
    """
    def __init__(self, query):
        self.query = self._format_query(query)

    @classmethod
    def execute(cls, df, expr):
        return cls(expr).execute_in_context(df)

    def execute_in_context(self, df):
        """ Execute the query in the context of a data frame.
        """
        try:
            return sqldf(self.query, {'df': df})
        except Exception as exc:
            return None

    def _format_query(self, query):
        parts = ['SELECT * FROM df']

        if query:
            parts.append('WHERE {}'.format(query))

        return ' '.join(parts) + ';'
