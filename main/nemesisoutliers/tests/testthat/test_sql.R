library(RSQLite)

context("sql")

sample_tbl_df <- data.frame(
  id = as.integer(c(2, 1, 3)),
  foo = c('a', 'a', 'b'),
  bar = c(0.0, 0.5, 1.0),
  baz = as.integer(c(T, F, T)), # SQLite does not have a real boolean type.
  stringsAsFactors = FALSE
)

test_that("a SQLite database can be rounded-tripped", {
  original <- list(
    sample_tbl = sample_tbl_df,
    second_tbl = data.frame(x=c(1,2,3), y=c(4,5,6)))
  
  path <- tempfile('sql.test.', fileext='.db')
  conn <- dbConnect(dbDriver('SQLite'), dbname=path)
  on.exit({ dbDisconnect(conn); unlink(path) })
  
  write_sql_db(conn, original)
  roundtripped <- read_sql_db(conn)
  expect_that(roundtripped, equals(original))
})

test_that("a CSV file can be copied to a SQLite database", {
  n = 100
  original = data.frame(
    id = seq.int(0,n-1),
    x = rbinom(n, 1, 0.5),
    y = runif(n)
  )
  
  in_path = tempfile('csv.in', fileext='.db')
  out_path = tempfile('sql.out', fileext='.db')
  out_conn = dbConnect(dbDriver('SQLite'), dbname=out_path)
  on.exit({
    dbDisconnect(out_conn)
    unlink(in_path); unlink(out_path);
  })
  
  write.csv(original, in_path, row.names=FALSE)
  copy_file_to_sql(in_path, out_conn, 'out_tbl', initial_rows=30)
  roundtripped = read_sql_db(out_conn, tables = 'out_tbl')[[1]]
  expect_that(roundtripped, equals(original))
})

test_that("a SQLite table can be copied to another SQLite database", {
  n = 100
  original = data.frame(
    id = seq.int(0,n-1),
    x = rbinom(n, 1, 0.5),
    y = runif(n)
  )
  
  in_path = tempfile('sql.in', fileext='.db')
  out_path = tempfile('sql.out', fileext='.db')
  in_conn = dbConnect(dbDriver('SQLite'), dbname=in_path)
  out_conn = dbConnect(dbDriver('SQLite'), dbname=out_path)
  on.exit({
    dbDisconnect(in_conn); dbDisconnect(out_conn);
    unlink(in_path); unlink(out_path);
  })
  
  write_sql_db(in_conn, list(in_tbl = original))
  copy_sql_to_sql(in_conn, 'in_tbl', out_conn, 'out_tbl', initial_rows=30)
  roundtripped = read_sql_db(out_conn, tables = 'out_tbl')[[1]]
  expect_that(roundtripped, equals(original))
})