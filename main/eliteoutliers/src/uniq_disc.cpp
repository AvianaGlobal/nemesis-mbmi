// [[Rcpp::plugins(cpp11)]]

#include <Rcpp.h>
#include "counts.hpp"
#include "dispatch.hpp"

using namespace Rcpp;

//' @name _uniq_disc
//' @rdname uniq_disc
template <typename T, typename U>
NumericVector _uniq_disc(std::vector<T> values, std::vector<U> groups, std::string type) {
  auto c = counts(values, groups);
  auto group_counts = c.second;
  
  int gn = group_counts.size();
  NumericVector out(gn);
  GenericVector names(gn);
  
  int i = 0;
  for (auto pair : group_counts) {
    auto grp = pair.second;
    
    if (type == "distinct") {
      out[i] = (grp.size() - 1) / ((double)group_size(grp) - 1);
    } else if (type == "frequent") {
      out[i] = max_group_count<T>(grp) / ((double)group_size(grp));
    } else {
      stop("Unknown unique_disc type: " + type);
    }
    
    names[i] = pair.first;
    i++;
  }

  out.attr("names") = names;
  return out;
}

//' Compute a ratio of the discrete unique values in each group.
//' 
//' @param \code{values} The vector of values
//' @param \code{groups} The vector of groups, corresponding to the values
//' @param \code{type} The type of ratio to compute: "distinct" or "frequent"
//' 
//' @return A numeric vector of the values for each group, named by group.
//' @export
// [[Rcpp::export]]
NumericVector uniq_disc(SEXP values, SEXP groups, std::string type) {
  std::initializer_list<SEXPTYPE> valid_types = {
    INTSXP, REALSXP, STRSXP, LGLSXP
  };
  
  if (!is_typeof(values, valid_types)) {
    stop("Invalid type for values vector");
  }
  
  if (!is_typeof(groups, valid_types)) {
    stop("Invalid type for groups vector");
  }
  
  return DISPATCH_GRP(_uniq_disc, NumericVector(), values, groups, type);
}