library(dplyr, warn.conflicts = FALSE)
library(RSQLite)

context("engine")

sample_csv_path <- system.file('extdata', 'sample_data.csv', package='EliteOutliers')
sample_db_path <- system.file('extdata', 'sample_data.db', package='EliteOutliers')

sample_data <- read.csv(sample_csv_path, stringsAsFactors = FALSE)

test_that("names are validated", {
  compute = function(df) df$foo
  expect_that(named_function('foo', compute)$name, equals('foo'))
  expect_that(named_function('foo bar', compute), throws_error('is_name'))
  expect_that(metric('.1', compute), throws_error('is_name'))
})

test_that("entity-level metrics are computed", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_metric(foo_plus = foo + 1)
  
  actual_values <- as.data.frame(run_model(sample_data)$entity_metric_values)
  desired_values <- as.data.frame(
    sample_data %>%
    mutate(foo_plus = foo + 1) %>%
    select(id, group_id, foo_plus)
  )

  expect_that(actual_values, equals(desired_values))
  
  # Entity scores are not persisted, so call 'score_entities' directly.
  actual_scores <- as.data.frame(score_entities(sample_data)$entity_metric_scores)
  desired_scores <- as.data.frame(
    sample_data %>%
    mutate(foo_plus = z_score(foo + 1)) %>%
    select(id, group_id, foo_plus)
  )
  expect_that(actual_scores, equals(desired_scores))
  
  # Check that capping the scores works.
  def_parameters(cap_entity_score = 1.0)
  actual_scores <- as.data.frame(score_entities(sample_data)$entity_metric_scores)
  desired_scores <- as.data.frame(
    sample_data %>%
    mutate(foo_plus = z_score(foo + 1, cap=1.0)) %>%
    select(id, group_id, foo_plus)
  )
  expect_that(actual_scores, equals(desired_scores))
})

test_that("factor variables are controlled", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_control(bar)
  def_metric(foo, control_for='bar')
  
  # Entity scores are not persisted, so call 'score_entities' directly.
  actual_scores <- as.data.frame(score_entities(sample_data)$entity_metric_scores)
  desired_scores <- as.data.frame(
    sample_data %>%
    group_by(bar) %>%
    mutate(foo = z_score(foo, cap=3.0)) %>%
    ungroup() %>%
    select(id, group_id, foo)
  )
  expect_that(actual_scores, equals(desired_scores))
})

test_that("group-level metrics are computed", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_metric(foo)
  
  actual_values <- as.data.frame(run_model(sample_data)$group_metric_values)
  desired_values <- as.data.frame(
    sample_data %>%
    group_by(group_id) %>%
    summarize(foo = Mean(foo))
  )
  expect_that(actual_values, equals(desired_values))
})

test_that("group-level group metrics are computed", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_group_metric('foo_bias', foo, function(values, groups) {
    mean_pop <- Mean(values)
    dt <- data.table(g=groups, v=values)
    dt <- dt[, list(.value = (Mean(v) - mean_pop)), by=c("g")]
    result <- dt$.value
    names(result) <- dt$g
    result
  })
  results <- run_model(sample_data)
  
  actual_values <- as.data.frame(results$group_metric_values)
  desired_values <- as.data.frame(
    sample_data %>%
    group_by(group_id) %>%
    do(foo_bias = Mean(.$foo) - Mean(sample_data$foo)) %>%
    summarize(group_id, foo_bias) %>%
    mutate(group_id=factor(group_id))
  )
  expect_that(actual_values, equals(desired_values))
  
  actual_scores <- as.data.frame(results$group_metric_scores)
  desired_scores <- as.data.frame(
    desired_values %>%
    mutate(foo_bias = z_score(foo_bias)) %>%
    select(group_id, foo_bias)
  )
  expect_that(actual_scores, equals(desired_scores))
})

test_that("group-level and composite scores are computed", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_metric(foo)
  def_composite_score(half_foo = 0.5 * foo)
  results <- run_model(sample_data)
  
  actual_metric_scores <- as.data.frame(results$group_metric_scores)
  desired_metric_scores <- as.data.frame(
    sample_data %>%
    mutate(foo = z_score(foo, cap=3.0)) %>%
    group_by(group_id) %>%
    summarize(foo = Mean(foo)) %>%
    mutate(foo = z_score(foo)) %>%
    select(group_id, foo)
  )
  expect_that(actual_metric_scores, equals(desired_metric_scores))
  
  actual_composite_scores <- as.data.frame(results$group_composite_scores)
  desired_composite_scores <- as.data.frame(
    desired_metric_scores %>%
    mutate(half_foo = 0.5 * foo) %>%
    select(group_id, half_foo)
  )
  expect_that(actual_composite_scores, equals(desired_composite_scores))
})

test_that("run summary is returned", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_metric(foo)
  results <- run_model(sample_data)
  
  run <- results$run_summary
  expect_equal(run['input_type',value], 'memory')
  expect_equal(run['entity_name',value], 'id')
  expect_equal(run['group_name',value], 'group_id')
})

test_that("summary statistics are computed for inputs and entity metrics", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_metric(foo_plus = foo + 1)
  results <- run_model(sample_data)
  
  input_stats <- results$input_stats
  expect_equal(input_stats['mean', foo], Mean(sample_data$foo))
  
  entity_stats <- results$entity_metric_stats
  expect_equal(entity_stats['mean', foo_plus], Mean(sample_data$foo+1))
  expect_equal(entity_stats['std', foo_plus], Sd(sample_data$foo+1))
})

test_that("small groups are filtered", {
  df <- tbl_df(data.frame(
    id = 1:10,
    group_id = c(rep('large_group', 8), rep('small_group', 2)),
    foo = runif(10),
    stringsAsFactors = FALSE))
  
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id',
                 min_group_size = 5)
  def_metric(foo)

  result <- run_model(df)
  target_attributes <- data.frame(
    group_id = c('large_group'),
    Size = as.integer(8))
  expect_equal(data.frame(result$group_attributes), target_attributes)
  expect_equal(unique(result$group_metric_values[,'group_id']),
               as.factor('large_group'))
})

test_that("engine supports different input types", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_control(bar)
  def_metric(foo_plus = foo + 1)
  def_metric(foo_bar = foo, control_for = 'bar')
  
  target_results = run_model(sample_data)
  check_results <- function(...) {
    # Don't compare the run summary tables.
    results = run_model(...)
    results[['run_summary']] = NULL
    target_results[['run_summary']] = NULL
    
    # XXX: Convert ffdf to data.frame to avoid complaint from all.equal about
    # "unclassing an external pointer" (Windows specific)
    expect_equal(lapply(results, as.data.frame),
                 lapply(target_results, as.data.frame))
  }
  
  check_results(input = list2env(sample_data)) # environment
  check_results(input = sample_csv_path) # CSV file
  
  # SQL database
  conn = dbConnect(dbDriver('SQLite'), dbname = sample_db_path)
  on.exit(dbDisconnect(conn))
  check_results(input = conn, input_table = 'data')
})

test_that("engine returns correct data types", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_metric(foo)
  def_metric(foo_plus = foo + 1)
  
  results = run_model(sample_data)
  expect_true(is.data.table(results$entity_metric_stats))
  expect_true(is.data.table(results$run_summary))  
  expect_true(is.ffdf(results$entity_metric_values))
  expect_true(is.ffdf(results$group_attributes))
  expect_true(is.ffdf(results$group_metric_values))
  expect_true(is.ffdf(results$group_metric_scores))
  expect_true(is.ffdf(results$group_composite_scores))
})

test_that("engine can store input data in output database", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_metric(foo)
  
  check_output <- function(...) {
    conn = dbConnect(dbDriver('SQLite'), dbname = ':memory:')
    on.exit(dbDisconnect(conn))
    
    run_model(..., output = conn, store_input = TRUE)
    recovered_data = dbReadTable(conn, 'input')
    recovered <- as.data.frame(recovered_data)

    # Ensure that the data frames have the same column ordering to prevent
    # a false negative.
    sample_cols <- colnames(sample_data)
    expect_equal(recovered[sample_cols], sample_data)
  }
  
  # check_output(input = sample_data) # data frame
  check_output(input = list2env(sample_data)) # environment
  check_output(input = sample_csv_path) # CSV file
  
  # SQL database
  conn = dbConnect(dbDriver('SQLite'), dbname = sample_db_path)
  on.exit(dbDisconnect(conn))
  check_output(input = conn, input_table = 'data')
})

test_that("engine does not re-copy input data unnecessarily", {
  reset_model()
  def_parameters(entity_name = 'id', group_name = 'group_id')
  def_metric(foo)
  
  conn = dbConnect(dbDriver('SQLite'), dbname = ':memory:')
  on.exit(dbDisconnect(conn))
  do_run <- function()
    run_model(input = sample_csv_path, output = conn,
              input_stats = TRUE, store_input = TRUE)
  do_run()
  sample_stats = dbReadTable(conn, 'input_stats')
  
  dbSendQuery(conn, 'DELETE FROM input')
  dbSendQuery(conn, 'DELETE FROM input_stats')
  do_run()
  expect_equal(nrow(dbReadTable(conn, 'input')), 0)
  expect_equal(nrow(dbReadTable(conn, 'input_stats')), 0)
  
  dbSendQuery(conn, "UPDATE run_summary SET value='other.csv' WHERE rn='input'")
  do_run()

  expect_equal(dbReadTable(conn, 'input'), sample_data)
  expect_equal(dbReadTable(conn, 'input_stats'), sample_stats)
  
  dbSendQuery(conn, 'DROP TABLE input')
  dbSendQuery(conn, 'DROP TABLE input_stats')
  do_run()
  expect_equal(dbReadTable(conn, 'input'), sample_data)
  expect_equal(dbReadTable(conn, 'input_stats'), sample_stats)
})