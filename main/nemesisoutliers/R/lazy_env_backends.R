#' Lazy environment from flat file
#' 
#' The objects in the environment are the columns of the file. Supports all
#' options of \code{fread} package in \code{data.table} package.
lazy_fread <- function(input, ...) {
  names = colnames(fread.df(input, nrows = 0, ...))
  promises = new.env()
  for (name in names) {
    expr = bquote(
      do.call(fread.df,
              c(list(.(input), select = .(name)), .(dots(...))),
              envir = .(parent.frame()))[[1]])
    assign(name, expr, promises)
  }
  lazy_env(promises)
}

fread.df <- function(...) fread(..., showProgress=F, verbose=F, data.table=F)

#' Lazy environment from SQL database
#' 
#' The objects in the environment are the columns of a table in the database.
#' 
#' @param \code{conn} DBI connection
#' @param \code{table_name} table to read from
lazy_sql <- function(conn, table_name, order_by = NULL) {
  # uid = 'dvs84291'
  # table_name = 'zip_profiles'
  # statement = paste0('select * from ', uid, '.', table_name, ' limit 0')
  # dbListTables(conn)
  # dbListFields(conn = conn, 'zip_profiles')
  # odbc::fetch(rs, -1)
  # odbc::dbClearResult(rs)
  # DBI::dbClearResult(rs)
  # names = fetch(dbSendQuery(statement = statement, conn = conn), -1)
  statement = paste0('select * from ', table_name, ' limit 0')
  rs = dbSendQuery(statement = statement, conn = conn)
  names = dbColumnInfo(rs)[[1]]
  if (is.null(order_by))
    order_by = names[[1]]
      
  promises = new.env()
  for (name in names) {
    query = paste('select', name, 'from', table_name, 'order by', order_by)
    expr = bquote(dbGetQuery(.conn, .(query))[[1]])
    assign(name, expr, promises)
  }
  env = lazy_env(promises)
  assign('.conn', conn, env)
  env
}

#' Lazy environment from data frame
#' 
#' The objects in the environment are the columns of the data frame.
#' The main use case is \code{ffdf}, though \code{data.frame} and 
#' \code{data.table} are also supported.
lazy_df <- function(df) {
  promises = new.env()
  for (name in colnames(df)) {
    expr = if (is.ffdf(df)) bquote(.df[,.(name)]) else bquote(.df[[.(name)]])
    assign(name, expr, promises)
  }
  env = lazy_env(promises)
  assign('.df', df, env)
  env
}