% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/lazy_env_backends.R
\name{lazy_df}
\alias{lazy_df}
\title{Lazy environment from data frame}
\usage{
lazy_df(df)
}
\description{
The objects in the environment are the columns of the data frame.
The main use case is \code{ffdf}, though \code{data.frame} and 
\code{data.table} are also supported.
}
