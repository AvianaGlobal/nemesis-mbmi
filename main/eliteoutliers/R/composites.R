#' @export
composite.pca <- function(env, top = 1, percent = TRUE) {
  library(dplyr)
  dt <- table_from_env(env)[, -1, with = FALSE] # Remove group key column
  dt <- select_if(dt, function(x){
    is.numeric(x) & # Remove non-numeric columns
      all(duplicated(x)[-1L]) == FALSE # Remove constant columns
  })
  pca <- prcomp(na.omit(dt), scale. = TRUE) # Run PCA
  var <- pca$sdev^2 
  prop <- var / sum(var)
  
  which_comps <- if (percent) {
    stopifnot(top >= 0 & top <= 1)
    
    under_top <- which(cumsum(prop) <= top)
    if (sum(prop[under_top]) < top) {
      next_top <- if (length(under_top) > 0) max(under_top) else 1
      c(under_top, next_top)
    } else {
      under_top
    }
  } else {
    stopifnot(top >= 1 & top <= length(prop))
    
    1:top
  }
  
  rowSums(pca$x[, which_comps, drop = FALSE])
}