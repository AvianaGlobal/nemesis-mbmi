% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/sql.R
\name{read_sql_db}
\alias{read_sql_db}
\title{Read multiple tables from SQL database}
\usage{
read_sql_db(conn, tables = NULL)
}
\arguments{
\item{\code{conn}}{DBI connection}

\item{\code{tables}}{tables to read (if omitted, all tables are read)}
}
\value{
List of data frames, one for each table
}
\description{
Read multiple tables from SQL database
}
\seealso{
\code{write_sql_db}
}
