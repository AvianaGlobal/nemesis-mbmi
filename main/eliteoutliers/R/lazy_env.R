#' Lazy environment
#' 
#' An environment that loads its objects lazily. Its main purpose is to create
#' wrappers around files or databases too large to fit comfortably in memory.
#' 
#' @return An object of class "lazy_env"
#' 
#' @seealso \code{lazy_fread}, \code{lazy_sql}
lazy_env <- function(promises) {
  env = new.env()
  copy_promises(promises, env)
  assign('.promises', promises, env)
  class(env) = c('lazy_env', 'environment')
  env
}

#' @rdname lazy_env
is_lazy_env <- function(x) {
  'lazy_env' %in% class(x)
}

# XXX: Only necessary on Windows?
names.lazy_env <- ls

#' Reset lazy environment
#' 
#' Removes all evaluated promises from memory.
#' 
#' @seealso \code{lazy_env}
reset_lazy_env <- function(env) {
  stopifnot(is_lazy_env(env))
  promises = get('.promises', env)
  copy_promises(promises, env)
  gc()
}

# Map function across lazy environment
lazy_map <- function(env, fn) {
  stopifnot(is_lazy_env(env))
  promises = get('.promises', env)
  fn_name = paste0('.fn.', paste(sample(letters,10), collapse=''))
  assign(fn_name, fn, env)
  for (name in ls(promises)) {
    expr = get(name, promises)
    mapped = bquote(.(as.name(fn_name))(.(expr)))
    assign(name, mapped, promises)
  }
  reset_lazy_env(env)
  env
}

copy_promises <- function(promises, env) {
  for (name in ls(promises)) {
    # XXX: This is convoluted, but nothing else seems to work.
    eval.env = new.env(parent = env)
    assign('expr', get(name, promises), eval.env)
    delayedAssign(name, eval(expr), eval.env = eval.env, assign.env = env)
  }
}

table_from_env <- function(data, names = NULL,
                           data.table = TRUE, stringsAsFactors = FALSE) {
  if (is.null(names))
    names = ls(data)
  cols = lapply(names, function(name) data[[name]])
  names(cols) = names
  if (data.table)
    as.data.table(cols)
  else
    as.data.frame(cols, stringsAsFactors = stringsAsFactors)
}