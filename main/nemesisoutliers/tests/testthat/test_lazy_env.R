library(RSQLite)

context('lazy_env')

sample_csv_path <- system.file('extdata', 'sample_tbl.csv', package='NemesisOutliers')
sample_db_path <- system.file('extdata', 'sample_tbl.db', package='NemesisOutliers')

test_that('lazy environments manage memory', {
  promises = new.env()
  assign('x', quote(seq(1e5)), promises)
  env = lazy_env(promises)
  orig_size = object_size(env)
  
  expect_false(is_lazy_env(promises))
  expect_true(is_lazy_env(env))
  
  get('x', env)
  size = object_size(env)
  expect_true(size > orig_size)
  
  reset_lazy_env(env)
  size = object_size(env)
  expect_equal(size, orig_size)
  
  get('x', env)
  size = object_size(env)
  expect_true(size > orig_size)
})

test_that('lazy environments map functions', {
  df = data.frame(x=c(1,2,3))
  env = lazy_df(df)
  
  env = lazy_map(env, function(x) 2*x)
  expect_equal(env[['x']], c(2,4,6))
  
  env = lazy_map(env, function(x) 10*x)
  expect_equal(env[['x']], c(20,40,60))
})

test_that('lazy reading of CSV file works', {
  sample_df = read.csv(sample_csv_path, stringsAsFactors = FALSE)
  
  env = lazy_fread(sample_csv_path)
  expect_equal(sort(ls(env)), sort(colnames(sample_df)))
  
  df = table_from_env(env, colnames(sample_df), data.table = FALSE)
  expect_equal(df, sample_df)
})

test_that('lazy reading of SQLite db works', {
  conn = dbConnect(dbDriver('SQLite'), dbname = sample_db_path)
  sample_df = dbReadTable(conn, 'sample_tbl')
  sample_df = sample_df[order(sample_df[,1]),] # Sort by first column
  row.names(sample_df) = NULL
  
  env = lazy_sql(conn, table = 'sample_tbl')
  expect_equal(sort(ls(env)), sort(colnames(sample_df)))
  
  df = table_from_env(env, colnames(sample_df), data.table = FALSE)
  expect_equal(df, sample_df)
})

test_that('lazy_reading of data frames works', {
  sample_df = read.csv(sample_csv_path, stringsAsFactors = FALSE)
  env = lazy_df(sample_df)
  expect_equal(sort(ls(env)), sort(colnames(sample_df)))
  expect_equal(table_from_env(env, colnames(sample_df), data.table = F),
               sample_df)
  
  sample_dt = fread(sample_csv_path)
  env = lazy_df(sample_dt)
  expect_equal(sort(ls(env)), sort(colnames(sample_dt)))
  expect_equal(table_from_env(env, colnames(sample_dt)),
               sample_dt)
  
  sample_ffdf = read.csv.ffdf(file = sample_csv_path)
  env = lazy_df(sample_ffdf)
  expect_equal(sort(ls(env)), sort(colnames(sample_ffdf)))
  expect_equal(table_from_env(env, colnames(sample_ffdf), data.table = F),
               as.data.frame(sample_ffdf))
})