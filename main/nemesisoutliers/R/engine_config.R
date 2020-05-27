# Data types --------------------------------------------------------------

# Constructor for "named_function" class
named_function <- function(name, compute) {
  stopifnot(is_name(name))
  structure(list(name=name, compute=compute), class="named_function")
}

# Constructor for "metric" class
metric <- function(name, compute, control_for=NULL) {
  stopifnot(is_name(name))
  structure(list(name=name, compute=compute, control_for=control_for),
            class="metric")
}

# Constructor for "metric.group" class
metric.group <- function(name, compute, compute.group) {
  stopifnot(is_name(name))
  structure(list(name=name, compute=compute, compute.group=compute.group),
            class="metric.group")
}

# Engine configuration ----------------------------------------------------

# Package-local engine environment. Stores the configuration.
engine_env <- new.env(parent = emptyenv())

add_engine_obj <- function(type, obj) {
  obj_list <- get(type, envir=engine_env)
  obj_list[[obj$name]] <- obj
  assign(type, obj_list, envir=engine_env)
}

#' Reset the model definition.
#' 
#' This erases all previously defined metrics and controls.
#' @export
reset_model <- function() {
  rm(list=ls(envir=engine_env), envir=engine_env)
  for (name in c("controls", "metrics", "metrics.group", "composites"))
    assign(name, list(), envir=engine_env)
}
reset_model()

#' Define global model parameters.
#' 
#' Supported parameters:
#' \itemize{
#'   \item \code{entity_name}: The column containing the entity ID (required).
#'   \item \code{group_name}: The column containing the group ID (required).
#'   \item \code{cap_entity_score}: Entity scores above this number 
#'    (in absolute value) will be capped (default = \code{Inf}).
#'   \item \code{min_group_size}: Groups with size smaller than this number
#'     will be discarded (default = \code{Inf}).
#' }
#' @export
def_parameters <- function(...) {
  params <- list(...)
  for (name in names(params))
    def_parameter_q(name, params[[name]])
}
#' @rdname def_parameters
#' @export
def_parameter_q <- function(name, value) {
  assign(name, value, envir=engine_env)
}

#' Define a control variable.
#' @export
def_control <- function(...) {
  named_fn <- auto_named_fn(dots(...), enclos=parent.frame())
  def_control_q(named_fn$name, named_fn$compute)
}
#' @rdname def_control
#' @export
def_control_q <- function(name, compute) {
  add_engine_obj("controls", named_function(name, compute))
}

#' Define a metric.
#' @export
def_metric <- function(..., control_for=NULL) {
  named_fn <- auto_named_fn(dots(...), enclos=parent.frame())
  def_metric_q(named_fn$name, named_fn$compute, control_for)
}
#' @rdname def_metric
#' @export
def_metric_q <- function(name, compute, control_for=NULL) {
  add_engine_obj("metrics", metric(name, compute, control_for))
}

#' Define a group metric.
#' 
#' A group metric is a special metric that does not produce entity and 
#' group scores in the ordinary way. Instead, the entity metric values are
#' combined at the group level by a function \code{compute.group} of three
#' arguments: the data table, the metric column name, and the group column name.
#' @export
def_group_metric <- function(name, compute, compute.group, ...) {
  compute_call <- substitute(compute)
  enclos <- parent.frame()
  compute <- function(df, ...) eval(compute_call, df, enclos)
  def_group_metric_q(name, compute, compute.group, ...)
}
#' @rdname def_group_metric
#' @export
def_group_metric_q <- function(name, compute, compute.group, ...) {
  obj <- metric.group(name, compute, function (values, groups) {
    compute.group(values, groups, ...)
  })
  add_engine_obj("metrics.group", obj)
}

#' Define a composite score.
#' @export
def_composite_score <- function(...) {
  named_fn <- auto_named_fn(dots(...), enclos=parent.frame())
  def_composite_score_q(named_fn$name, named_fn$compute)
}
#' @rdname def_composite_score
#' @export
def_composite_score_q <- function(name, compute, ...) {
  obj <- named_function(name, function(df) compute(df, ...))
  add_engine_obj("composites", obj)
}

# Utility functions -------------------------------------------------------

auto_named_fn <- function(alist, enclos=NULL) {
  if (!(length(alist) == 1))
    stop('must supply exactly one expression')
  
  expr <- alist[[1]]
  if (is.null(names(alist)))
    name <- make.names(deparse(expr))
  else
    name <- names(alist)
  
  compute <- function(envir) eval(expr, envir, enclos)
  named_function(name=name, compute=compute)
}

is_name <- function(name) name == make.names(name)