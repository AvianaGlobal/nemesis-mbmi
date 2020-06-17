#' Read multiple tables from SQL database
#' 
#' @param \code{conn} DBI connection
#' @param \code{tables} tables to read (if omitted, all tables are read)
#'  
#' @return List of data frames, one for each table
#' 
#' @seealso \code{write_sql_db}
read_sql_db <- function(conn, tables = NULL) {
  if (is.null(tables))
    tables <- dbListTables(conn)
  result <- list()
  for (table_name in tables) {
    df <- dbReadTable(conn, table_name)
    attr(df, 'row.names') <- c(1:nrow(df)) # By default, SQLite uses char.
    result[[table_name]] <- df
  }
  result
}

#' Write multiple tables to a SQL database
#' 
#' @param \code{conn} DBI connection
#' 
#' @param \code{tables} list of data tables, each of one of the following types:
#' \itemize{
#'   \item data frame (including data.table and ffdf)
#'   \item environment
#' }
#' 
#' @details
#' Warning: if any of the tables already exist, they will be dropped!
#' 
#' @seealso \code{read_sql_db}
write_sql_db <- function(conn, tables) {
  if (is.null(names(tables)))
    stop('The tables must be named.')
  
  for (name in names(tables)) {
    if (dbExistsTable(conn, name))
      dbRemoveTable(conn, name)
    
    value <- tables[[name]]
    if (is.environment(value))
      value <- table_from_env(value, data.table = FALSE)
    if (is.ffdf(value))
      write.dbi.ffdf(value, name, conn, row.names = FALSE)
    else if (ncol(value) > 0 & nrow(value) > 0)
      dbWriteTable(conn, name, value, row.names = FALSE)
  }
}

#' Copy file to SQL table
#' 
#' Copy a flat file to a table in a SQL database.
#' 
#' @param \code{in_file} input path or connection
#' @param \code{out_conn} database to copy to (DBI connection)
#' @param \code{out_table} name of table to copy to
#' @param \code{initial_rows} number of lines to read in first batch
#' @param \code{batch_bytes} size of subsequent batches in bytes
#' @param \code{...} arguments to pass to \code{fread} (see details)
#' 
#' @details The copy is performed by reading the data from the input file to
#' memory, then pushing it from memory to the output DB. To avoid excessive
#' memory usage, the file is read in batches.
#' 
#' Technically, this functionality is already built into \code{dbWriteTable}.
#' However, that implementation uses the DB-specific import function, which
#' can be unreliable. For example, SQLite cannot handle column separators
#' inside quotes. For consistency and reliability, we use \code{fread} from the
#' \code{data.table} package to parse the input file.
copy_file_to_sql <- function(in_file, out_conn, out_table,
                             initial_rows = 1e4L,
                             batch_bytes = getOption("ffbatchbytes"), ...) {
  # Validate inputs.
  if (is.character(in_file)) {
    in_conn = file(in_file, 'r')
    on.exit(close(in_conn))
  } else if ('connection' %in% class(in_file)) {
    in_conn = in_file
    stopifnot(isOpen(in_conn))
  } else
    stop('Input file is not a character vector or connection')
  stopifnot(is(out_conn, 'DBIConnection'))
  
  if (dbExistsTable(out_conn, out_table))
    dbRemoveTable(out_conn, out_table)
  
  # Copy first batch.
  read_lines = function(n) {
    paste(readLines(in_conn, n=n, ok=TRUE, warn=FALSE), collapse='\n')
  }
  lines = read_lines(initial_rows)
  df = fread(input=lines, ...)
  row_bytes = object.size(df) / nrow(df)
  next_rows = as.integer(batch_bytes / row_bytes)
  dbWriteTable(out_conn, out_table, df, row.names = FALSE)
  input_cols <- colnames(df)
  rm(lines); rm(df); gc()
  
  # Copy remaining batches.
  repeat {
    lines = read_lines(next_rows)
    if (nchar(lines) == 0)
      break
    df = fread(input=lines, header=FALSE, col.names=input_cols, ...)
    dbWriteTable(out_conn, out_table, df, append = TRUE, row.names = FALSE)
    rm(lines); rm(df); gc()
  }
}

#' Copy SQL table
#' 
#' Copy a table from one SQL database to another.
#' 
#' @param \code{in_conn} database to copy from (DBI connection)
#' @param \code{in_table} name of table to copy from
#' @param \code{out_conn} database to copy to (DBI connection)
#' @param \code{out_table} name of table to copy to
#' @param \code{initial_rows} number of rows to read in first batch
#' @param \code{batch_bytes} size of subsequent batches in bytes
#' 
#' @details The copy is performed by fetching the data from the input DB to
#' memory, then pushing it from memory to the output DB. To avoid excessive
#' memory usage, the table is read in batches.
#' 
#' Warning: if the output table already exists, it will be dropped!
copy_sql_to_sql <- function(in_conn, in_table, out_conn, out_table,
                            initial_rows = 1e4L,
                            batch_bytes = getOption("ffbatchbytes")) {
  stopifnot(is(in_conn, 'DBIConnection') && is(out_conn, 'DBIConnection'))
  if (dbExistsTable(out_conn, out_table))
    dbRemoveTable(out_conn, out_table)
  
  # Send query to input DB.
  query = paste('select * from', in_table)
  res = dbSendQuery(in_conn, query)
  
  # Copy first batch.
  df = dbFetch(res, n=initial_rows)
  row_bytes = object.size(df) / nrow(df)
  next_rows = as.integer(batch_bytes / row_bytes)
  dbWriteTable(out_conn, out_table, df)
  rm(df); gc()
  
  # Copy remaining batches.
  repeat {
    df = dbFetch(res, n=next_rows)
    if (nrow(df) == 0)
      break
    dbWriteTable(out_conn, out_table, df, append = TRUE)
    rm(df); gc()
  }
  dbClearResult(res)
}

# Hacks -------------------------------------------------------------

# https://github.com/hadley/dplyr/issues/969
setOldClass(c('tbl_df', 'data.frame'))
setOldClass(c('tbl_dt', 'data.table'))

# Ripped from ETLUtils and modified to:
#   1. Fix a bug: https://github.com/jwijffels/ETLUtils/pull/1
#   2. Accept a DBI connection (rather than the silly `dbConnect.args`)
write.dbi.ffdf <- function(x, name, conn,
                           RECORDBYTES = sum(.rambytes[vmode(x)]), 
                           BATCHBYTES = getOption("ffbatchbytes"),
                           by = NULL,
                           VERBOSE = FALSE,
                           ...){
  stopifnot(inherits(x, "ffdf"))
  stopifnot(nrow(x) > 0)
  
  chunks <- ff::chunk.ffdf(x, RECORDBYTES=RECORDBYTES, BATCHBYTES=BATCHBYTES, by=by)
  for(i in seq_along(chunks)){
    if (VERBOSE){
      cat(sprintf("%s dbWriteTable chunk %s/%s\n", Sys.time(), i, length(chunks)))
    } 
    chunkidx <- chunks[[i]]
    dbWriteTable.args <- list(...)
    dbWriteTable.args$conn <- conn
    dbWriteTable.args$name <- name
    dbWriteTable.args$value <- x[chunkidx, , drop=FALSE]
    if(i > 1 && "overwrite" %in% names(dbWriteTable.args)){
      dbWriteTable.args$overwrite <- FALSE
    }
    if(i > 1){
      dbWriteTable.args$append <- TRUE
    }
    do.call('dbWriteTable', dbWriteTable.args)
  }
  invisible()
}

# Lifted from https://github.com/rstats-db/DBI/pull/34
# TODO: Once the PR is merged, remove this code and update DBI.
setGeneric("dbCreateIndex", 
           def = function(conn, tablename, cols, indexname = NULL, ...)
             standardGeneric("dbCreateIndex")
)
setMethod("dbCreateIndex", signature("DBIConnection", "character"), 
          function(conn, tablename, cols, indexname = NULL, ...) {
            # following naming conventions here:
            # http://stackoverflow.com/questions/2783495/sql-server-index-naming-conventions
            if (is.null(indexname)) {
              indexname <- paste("ix", tablename, paste0(cols, collapse = "_"), sep = "_")
            }
            statement = paste("CREATE INDEX", indexname, "ON", tablename, 
                              "(", paste0(cols, collapse = ","), ")", sep = " ")
            rs <- dbSendQuery(conn, statement, ...)
          }
)