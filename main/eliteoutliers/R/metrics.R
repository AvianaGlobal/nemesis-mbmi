# Metric implementations

#' @export
ratio <- function(x, y, min=NULL, min_to=NULL, max=NULL, max_to=NULL,
                  zero_to=NULL, inf_to=NULL, na_to=NULL) {
  result = x/y
  
  if (!is.null(min)) {
    min_to <- if(is.null(min_to)) min else min_to
    result[result < min] <- min_to
  }
  if (!is.null(max)) {
    max_to <- if(is.null(max_to)) max else max_to
    result[result > max] <- max_to
  }
  
  if (!is.null(zero_to))
    result[result == 0] <- zero_to
  if (!is.null(inf_to))
    result[is.infinite(result) | is.nan(result)] <- inf_to
  if (!is.null(na_to))
    result[is.na(result)] <- na_to
  
  result
}

#' @export
safe_log1p <- function(x) {
  sign(x) * log1p(abs(x))
}
