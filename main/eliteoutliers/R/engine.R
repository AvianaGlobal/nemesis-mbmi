# Engine execution --------------------------------------------------------

#' Run the model
#' 
#' Runs the model on the specified input data. 
#' 
#' @param \code{input} input data source, of one of the following types:
#' \itemize{
#'  \item data frame
#'  \item environment
#'  \item filename (supported file types: CSV, TSV)
#'  \item SQL database (DBI connection)
#' }
#' 
#' @param \code{input_table} name of table containing input data.
#'  Only applicable when input source is a SQL database.
#'
#' @param \code{input_stats} whether to compute summary statistics for input
#'   data columns (default: yes)
#'  
#' @param \code{output} output database (DBI connection, optional)
#' 
#' @param \code{create_indices} whether to create group indices in the 
#'  entity-level tables of the output DB (default: yes)
#' 
#' @param \code{store_input} whether to save the input data as an additional
#'  table in the output DB (default: no)
#' 
#' @param \code{env} environment containing the model configuration
#'  (default: the global model environment)
#' 
#' @return A named list with the following data frames:
#' \enumerate{
#'  \item \code{run_summary}:
#'    A table of key-value pairs summarizing the run.
#' 
#'  \item \code{entity_metric_values}:
#'    Entity-level metric values. Group metrics are not included.
#' 
#'  \item \code{entity_metric_stats}:
#'    Population statistics of entity-level metric values. The columns are
#'    metrics and the rows are summary statistics.
#'    
#'    No statistics are computed for group metrics.
#'  
#'  \item \code{group_attributes}:
#'    General attributes of the group. At present, this only includes the size
#'    of the group.
#'  
#'  \item \code{group_metric_values}:
#'    Group-level metric values. For non-group metrics, these are simply
#'    the means of the entity-level metric values.
#'  
#'  \item \code{group_metric_scores}:
#'    Group-level metric scores
#'  
#'  \item \code{group_composite_scores}:
#'    Group-level composite scores
#'  
#'  \item \code{input_stats}:
#'    Population statistics for input data. The columns are inputs and the rows
#'    are summary statistics.
#' }
#' The tables \code{run_summary}, \code{input_stats}, and
#' \code{entity_metric_stats} have type \code{data.table}.
#' All other tables have type \code{ffdf}.
#' 
#' @export
run_model <- function(input, input_table=NULL, input_stats=TRUE, output=NULL,
                      create_indices=TRUE, store_input=FALSE, env=NULL) {
  # Validate function parameters.
  if (is.data.frame(input) || is.environment(input))
    data = input
  else if (is.character(input))
    data = lazy_fread(input)
  else if (is(input, 'DBIConnection')) {
    stopifnot(!is.null(input_table))
    data = lazy_sql(input, input_table)
  } else
    stop('Unknown input type', str(input))
  if (!is.null(output))
    stopifnot(is(output, 'DBIConnection'))
  if (is.null(env))
    env <- engine_env
  
  # Validate model parameters.
  in_env <- function(name) exists(name, envir=env, inherits=FALSE)
  if(!(in_env('entity_name') & in_env('group_name')))
    stop('Must supply entity and group column names')
  else if(!all(c(env$entity_name, env$group_name) %in% ls(data)))
    stop('Invalid entity or group column name')
  
  # Create run metadata table.
  run_summary <- summarize_run(input, input_table, env)
  
  # Determine whether the input needs to be copied and/or summarized.
  if (!is.null(output) && (input_stats || store_input) && 
      run_summary['input_type'] != 'memory' &&
      dbExistsTable(output, 'run_summary')) {
    old_run_summary = setDT(dbReadTable(output, 'run_summary'))
    setkey(old_run_summary, 'rn')
    cmp = c('input', 'input_type')
    if (all(run_summary[cmp,] == old_run_summary[cmp,])) {
      if (dbExistsTable(output, 'input'))
        store_input = FALSE
      if (dbExistsTable(output, 'input_stats'))
        input_stats = FALSE
    }
  }
  
  # Filter small groups.
  if (in_env('min_group_size')) {
    dt = table_from_env(data, env$group_name)
    dt[, .indices := .N >= env$min_group_size, by = c(env$group_name)]
    if (is.data.frame(data))
      data = lazy_df(data)
    data = lazy_map(data, function(x) x[dt$.indices])
  }
  
  # Perform the computations!
  if (input_stats)
    input_stats_dt <- summary_stats(data, env)
  entity_results <- score_entities(data, env)
  rm(data); gc()
  entity_stats <- summary_stats(entity_results$entity_metric_values, env)
  group_results <- score_groups(entity_results, env)
  group_attributes <- summarize_groups(entity_results, group_results, env)
  
  # Build the return list.
  cast_dt <- function(z) if (is.ffdf(z)) table_from_ffdf(z, colnames(z)) else z
  Merge <- function(x, y, ...) {
    merge(cast_dt(x), cast_dt(y), ..., by=env$group_name, all=TRUE)
  }
  
  group_combined <- Merge(group_results$group_metric_values,
                          group_results$group_metric_scores,
                          suffixes=c('', '_Score'))
  group_combined <- Merge(group_combined, group_results$group_composite_scores)
  group_combined <- Merge(group_combined, group_attributes)
  
  metadata <- function(df, type, exclude=NULL, suffix='') {
    cols <- colnames(df)
    if (!is.null(exclude)) {
      idx <- which(cols %in% exclude)
      if (length(idx) > 0)
        cols <- cols[-idx]
    }
    
    if (length(cols) > 0) {
      get_class <- function(col) class(cast_dt(df)[[col]])
      data.frame(name=paste0(cols, suffix), type=type, dtype=sapply(cols, get_class))
    } else data.frame()
  }
  
  group_metadata <- function(...) metadata(..., exclude=env$group_name)
  
  group_metadata <- rbind(
    group_metadata(group_results$group_metric_values, 'metric_value'),
    group_metadata(group_results$group_metric_scores, 'metric_score', suffix='_Score'),
    group_metadata(group_results$group_composite_scores, 'composite_score'),
    group_metadata(group_attributes, 'attribute')
  )
  
  colnames(entity_results$entity_metric_scores) <- sapply(colnames(entity_results$entity_metric_scores), function(name) {
    if (name %in% c(env$entity_name, env$group_name)) {
      name
    } else {
      paste(name, '_Score', sep='')
    }
  })
  
  results = list(run_summary = run_summary,
                 entity_metric_values = entity_results$entity_metric_values,
                 entity_metric_scores = entity_results$entity_metric_scores,
                 entity_metric_stats = entity_stats,
                 group_results=group_combined,
                 group_metadata=group_metadata)
  if (input_stats)
    results$input_stats = input_stats_dt
  
  # Save the results to the output DB.
  if (!is.null(output)) {
    # Save output tables.
    write_sql_db(output, results)
    
    # Save input table, if necessary.
    if (store_input) {
      if (is.character(input))
        copy_file_to_sql(input, output, 'input')
      else if (is(input, 'DBIConnection'))
        copy_sql_to_sql(input, input_table, output, 'input')
      else 
        write_sql_db(output, list(input = input))
    }
    
    # Create DB indices.
    if (create_indices) {
      dbCreateIndex(output, 'group_results', env$group_name)
      if (store_input)
        dbCreateIndex(output, 'input', env$group_name)
    }
  }
  
  results
}

summary_stats <- function(data, env=NULL) {
  if (is.null(env)) env <- engine_env
  
  summarize_numeric <- function(x) {
    base <- c(mean = Mean(x), std = Sd(x))
    quantiles <- Quantile(x, names=FALSE)
    names(quantiles) <- c('min', '25%', '50%', '75%', 'max')
    return(c(base, quantiles))
  }
  summarize <- function(x) {
    if (is.logical(x) || is.numeric(x)) summarize_numeric(x)
    else NULL
  }
  
  # Compute summary statistics for each column.
  nms = if (is.ffdf(data)) colnames(data) else ls(data)
  nms = setdiff(nms, c(env$entity_name, env$group_name))
  cols = lapply(setNames(nm = nms), function(name) {
    col = if (is.ffdf(data)) data[,name] else data[[name]]
    result = summarize(col)
    if (is_lazy_env(data))
      reset_lazy_env(data)
    result
  })
  
  # Package summary statistics as data table.
  cols = Filter(Negate(is.null), cols)
  if (length(cols) == 0)
    return(data.table())
  dt = as.data.frame(cols)
  setDT(dt, keep.rownames = TRUE)
  setkey(dt, rn)
  dt
}

score_entities <- function(data, env=NULL) {
  if (is.null(env)) env <- engine_env
  
  # Compute the entity-level control and metric values.
  id_names = c(env$entity_name, env$group_name)
  id_df = as.ffdf(table_from_env(data, id_names, data.table = FALSE,
                                 stringsAsFactors = TRUE))
  entity_df = id_df
  for (obj in c(env$controls, env$metrics, env$metrics.group)) {
    value = obj$compute(data)
    entity_df = cbind(entity_df, ffdf_from_mem(obj$name, value))
    if (is_lazy_env(data))
      reset_lazy_env(data)
  }
  
  # Compute the entity-level metric scores.
  entity_score_df = id_df
  cap = if (exists('cap_entity_score', env, inherits=FALSE))
    env$cap_entity_score else NULL
  metric_score = function(x) z_score(x, cap=cap)
  for (metric in env$metrics) {
    controls = as.character(metric$control_for)
    dt = table_from_ffdf(entity_df, c(metric$name,controls))
    dt[, .score := metric_score(get(metric$name)), by = c(controls)]
    col_df = ffdf_from_mem(metric$name, dt$.score)
    entity_score_df = cbind(entity_score_df, col_df)
    rm(dt); gc()
  }
  
  return(list(entity_metric_values = entity_df,
              entity_metric_scores = entity_score_df))
}

eval_groups <- function(entity_metrics, env) {
  metric_values <- NULL
  
  do_metric <- function(metric, group_func) {
    dt <- table_from_ffdf(entity_metrics, c(env$group_name, metric$name))
    dt <- group_func(dt)
    result <- merge_ffdf_dt(metric_values, dt, by = env$group_name)
    rm(dt); gc()
    result
  }
  
  # Compute the group-level values for standard metrics.
  for (metric in env$metrics) {
    metric_values <- do_metric(metric, function(dt) {
      dt <- dt[, list(.value = Mean(get(metric$name))), by = c(env$group_name)]
      setnames(dt, '.value', metric$name)
      dt
    })
  }
  
  # Compute the group-level values for group metrics.
  for (metric in env$metrics.group) {
    metric_values <- do_metric(metric, function (dt) {
      result <- metric$compute.group(dt[[metric$name]], dt[[env$group_name]])
      dt <- data.table(factor(names(result)), result)
      setnames(dt, c(env$group_name, metric$name))
      dt
    })
  }
  metric_values
}

score_groups <- function(entity_results, env=NULL) {
  if (is.null(env)) env <- engine_env
  
  # Compute the group-level metric values.
  group_values <- eval_groups(entity_results$entity_metric_values, env)
  
  # Compute the group-level metric scores.
  entity_scores = entity_results$entity_metric_scores
  group_scores = group_values[env$group_name]
  for (metric in env$metrics) {
    dt = table_from_ffdf(entity_scores, c(env$group_name, metric$name))
    dt = dt[, list(.score = Mean(get(metric$name))), by = c(env$group_name)]
    dt[, .score := z_score(.score)]
    setnames(dt, '.score', metric$name)
    group_scores = merge_ffdf_dt(group_scores, dt, by = env$group_name)
    rm(dt); gc()
  }
  for (metric in env$metrics.group) {
    col_df = ffdf_from_mem(metric$name, z_score(group_values[,metric$name]))
    group_scores = cbind(group_scores, col_df)
  }
  
  # Compute the composite scores.
  composite_scores = group_scores[env$group_name]
  group_scores_env = lazy_df(group_scores)
  for (composite in env$composites) {
    col_df = ffdf_from_mem(composite$name, composite$compute(group_scores_env))
    composite_scores = cbind(composite_scores, col_df)
    reset_lazy_env(group_scores_env)
  }
  
  return(list(group_metric_values = group_values,
              group_metric_scores = group_scores,
              group_composite_scores = composite_scores))
}

summarize_groups <- function(entity_results, group_results, env) {
  entity_metrics = entity_results$entity_metric_values
  group_metrics = group_results$group_metric_values
  
  dt = table_from_ffdf(entity_metrics, env$group_name)
  dt = dt[,list(Size = .N), by=c(env$group_name)]
  setkeyv(dt, env$group_name)
  merge_ffdf_dt(group_metrics[env$group_name], dt, by = env$group_name)
}

summarize_run <- function(input, input_table=NULL, env=NULL) {
  if (is.null(env)) env <- engine_env
  
  if (is.character(input)) {
    input_str = input
    input_type = 'file'
  } else if (is(input, 'DBIConnection')) {
    slots = intersect(c('dbname', 'user', 'host'), slotNames(input))
    input_info = c(list(class = class(input)),
                   lapply(setNames(nm=slots), function(s) slot(input,s)),
                   list(table = input_table))
    input_str = deparse(input_info, control=NULL, width.cutoff=500)
    input_type = 'sql'
  } else {
    #input_str = paste(capture.output(str(input)), collapse='\n')
    input_str = ':memory:'
    input_type = 'memory'
  }
  
  summary_data <- list(
    date = date(),
    platform = R.version$platform,
    package_version = as.character(packageVersion('EliteOutliers')),
    r_version = R.version.string,
    input = input_str,
    input_type = input_type,
    entity_name = env$entity_name,
    group_name = env$group_name
  )
  data.table(rn = names(summary_data),
             value = unname(as.character(summary_data)),
             key = 'rn')
}

# Utility functions -------------------------------------------------------

# https://github.com/edwindj/ffbase/issues/36
#' @export
cbind.ffdf <- function(df1, df2) {
  result <- do.call('ffdf', c(physical(df1), physical(df2)))
  colnames(result) <- c(colnames(df1), colnames(df2))
  result
}

# ff does not support character vectors, only factors
ff_cast <- function(x, ...) {
  if (is.character(x))
    x = as.factor(x)
  ff(x, ...)
}

ffdf_from_mem <- function(name, value) {
  df = ffdf(value = ff_cast(value))
  colnames(df) = name
  df
}

merge_ffdf_dt <- function(df, dt, by) {
  if (is.null(dt)) return(df)
  setkeyv(dt, by)
  if (is.null(df)) return(as.ffdf(dt))
  cbind.ffdf(df, as.ffdf(dt[, !by, with=FALSE]))
}

table_from_ffdf <- function(df, cols) {
  dt = df[, cols, drop = FALSE]
  setDT(dt)
  dt
}