# General-purpose statistical functions

#' Missing value variants
#' 
#' These functions are variants of the standard R functions that ignore
#' missing values.
#' 
#' @rdname na_variants
Mean <- function(x, ...) mean(x, na.rm=TRUE, ...)
#' @rdname na_variants
Sd <- function(x) sd(x, na.rm=TRUE)
#' @rdname na_variants
Scale <- function(x) (x - Mean(x)) / Sd(x)
#' @rdname na_variants
Quantile <- function(x, ...) quantile(x, na.rm=TRUE, ...)

#' Kolmogorov-Smirnov statistic
#' 
#' Computes the Kolmogorov-Smirnov statistic for numerical data.
#' 
#' @details Unlike \code{ks.test}, this function supports both continuous and 
#' discrete numerical data. However, since the p-values are not reliable in the
#' latter case, no p-values are computed.
#' 
#' @export
ks.stat <- function(x, y) {
  x.cdf <- ecdf(x)
  y.cdf <- ecdf(y)
  cdf.diff <- sapply(unique(c(x,y)), function(v) x.cdf(v) - y.cdf(v))
  max(abs(cdf.diff))
}

#' Z score
#' 
#' Unlike \code{scale}, this function ignores missing values. Also, the scores
#' may be capped at some threshold value.
z_score <- function(x, cap=NULL) {
  z = Scale(x)
  if (!is.null(cap)) {
    z[z > cap] = cap
    z[z < -cap] = -cap
  }
  return(z)
}
