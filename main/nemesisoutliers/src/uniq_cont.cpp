// [[Rcpp::plugins(cpp11)]]

#include <Rcpp.h>
#include "dispatch.hpp"
#include "groups.hpp"

using namespace Rcpp;

/*
 * Compute the covariance of a numeric vector.
 */
double cov(NumericVector v) {
  NumericVector no_na = na_omit(v);
  return sd(no_na) / mean(no_na);
}

//' @name _uniq_cont
//' @rdname uniq_cont
template <typename T>
NumericVector _uniq_cont(std::vector<double> values, std::vector<T> groups) {
  int n, i;
  
  auto grouped = group(values, groups);
  n = grouped.size();
  
  auto pop = NumericVector(values.begin(), values.end());
  auto pop_cov = cov(pop);
  
  NumericVector out(n);
  GenericVector names(n);
  
  i = 0;
  for (auto pair : grouped) {
    auto grp = NumericVector(pair.second.begin(), pair.second.end());
    out[i] = cov(grp) / pop_cov;
    names[i] = pair.first;
    
    i++;
  }
  
  out.attr("names") = names;
  return out;
}

//' Computes the ratio of the coefficient of variation for each group to the
//' population.
//' 
//' @param \code{values} The vector of values
//' @param \code{groups} The vector of groups, corresponding to the values
//' 
//' @return A numeric vector of the ratio values for each group, named by group.
//' @export
// [[Rcpp::export]]
NumericVector uniq_cont(SEXP values, SEXP groups) {
  if (!is_typeof(values, {INTSXP, REALSXP})) {
    stop("Invalid type for values vector");
  }

  if (!is_typeof(groups, {INTSXP, REALSXP, STRSXP, LGLSXP})) {
    stop("Invalid type for groups vector");
  }
  
  switch (TYPEOF(groups)) {
  case INTSXP:
    return _uniq_cont(AS_VEC(double, values), AS_VEC(int, groups));
  case REALSXP:
    return _uniq_cont(AS_VEC(double, values), AS_VEC(double, groups));
  case STRSXP:
    return _uniq_cont(AS_VEC(double, values), AS_VEC(std::string, groups));
  case LGLSXP:
    return _uniq_cont(AS_VEC(double, values), AS_VEC(bool, groups));
  }
  
  return NumericVector();
}
