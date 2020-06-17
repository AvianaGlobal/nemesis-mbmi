// [[Rcpp::plugins(cpp11)]]

#include <Rcpp.h>
#include "counts.hpp"
#include "groups.hpp"
#include "dispatch.hpp"

using namespace Rcpp;

/**
 * Calculate the number of r-combinations of n elements.
 * Source: http://stackoverflow.com/questions/9330915/number-of-combinations-n-choose-r-in-c
 */
unsigned choose(unsigned n, unsigned k) {
  if (k > n) return 0;
  if (k * 2 > n) k = n-k;
  if (k == 0) return 1;
  
  int result = n;
  for( int i = 2; i <= k; ++i ) {
    result *= (n-i+1);
    result /= i;
  }
  
  return result;
}

//' @name _graph_density
//' @rdname graph_density
template <typename T, typename U>
NumericVector _graph_density(std::vector<T> values, std::vector<U> groups) {
  auto grouped = group(values, groups);

  int gn = grouped.size();
  NumericVector out(gn);
  GenericVector names(gn);

  int i = 0;
  for (auto pair : grouped) {
    auto grp = pair.second;
    
    int links = 0;
    auto subgroup_cnts = count_unique(grp);
    for (auto subpair : subgroup_cnts) {
      int cnt = subpair.second;
      if (cnt > 1) {
        links += choose(cnt, 2);
      }
    }
    
    int links_possible = choose(grp.size(), 2);
    out[i] = links_possible == 0 ? 0 : links / ((double)links_possible);
    names[i] = pair.first;
    i++;
  }

  out.attr("names") = names;
  return out;
}

//' Compute a value of the density of the links between the values in each
//' group.
//' 
//' @param \code{values} The vector of values
//' @param \code{groups} The vector of groups, corresponding to the values
//' 
//' @return A numeric vector of the values for each group, named by group.
//' @export
// [[Rcpp::export]]
NumericVector graph_density(SEXP values, SEXP groups) {
  std::initializer_list<SEXPTYPE> valid_types = {
    INTSXP, REALSXP, STRSXP, LGLSXP
  };
  
  if (!is_typeof(values, valid_types)) {
    stop("Invalid type for values vector");
  }
  
  if (!is_typeof(groups, valid_types)) {
    stop("Invalid type for groups vector");
  }
  
  return DISPATCH_GRP(_graph_density, NumericVector(), values, groups);
}