// [[Rcpp::plugins(cpp11)]]

#include <Rcpp.h>
#include "counts.hpp"
#include "dispatch.hpp"

using namespace Rcpp;

//' Compute the Pearson Chi-Squared statistic.
//' 
//' @name chisq_pearson
//' 
//' @param \code{d} The observed vector
//' @param \code{e} The expected vector
//' 
//' @return The computed value of the statistic
double chisq_pearson(NumericVector &d, NumericVector &e) {
  double result;
  int i;
  
  if (d.size() != e.size()) return NAN;
  
  result = 0.0;
  for (i = 0; i < d.size(); i++) {
    result += pow(d[i] - e[i], 2) / e[i];
  }
  
  return result;
}

//' @name _chisq_test
//' @rdname chisq_test
template <typename T, typename U>
NumericVector _chisq_test(std::vector<T> values, std::vector<U> groups) {
  Function pchisq = Function("pchisq");
  int pn, gn, i, j;
  
  auto c = counts(values, groups);
  auto pop_counts = c.first;
  auto group_counts = c.second;

  pn = pop_counts.size();
  NumericVector popv(pn);
  
  gn = group_counts.size();
  NumericVector out(gn);
  GenericVector names(gn);
  
  i = 0;
  for (auto p : pop_counts) {
    popv[i] = p.second;
    i++;
  }
  
  j = 0;
  for (auto g : group_counts) {
    NumericVector groupv(pn);
    NumericVector adj_popv(pn);
    int poplen = values.size();
    int grplen = group_size(g.second);

    i = 0;
    for (auto p : pop_counts) {
      groupv[i] = g.second[p.first];
      adj_popv[i] = grplen * popv[i] / poplen;
      i++;
    }

    auto p = as<double>(
      pchisq(chisq_pearson(groupv, adj_popv), pn - 1, _["lower.tail"] = false)
    );
    
    out[j] = 100 * (1 - p);
    names[j] = g.first;
    
    j++;
  }
  
  out.attr("names") = names;
  return out;
}

//' Compute the Chi-Squared statistic for a given column, grouped by another column.
//' 
//' @description Computes (1 - p-value) * 100 for each group, using a
//' Chi-Squared statistic to obtain the p-value.
//' 
//' @param \code{values} The vector of values
//' @param \code{groups} The vector of groups, corresponding to the values
//' 
//' @return A numeric vector of the statistic values for each group, named by group.
//' @export
// [[Rcpp::export]]
NumericVector chisq_test(SEXP values, SEXP groups) {
  std::initializer_list<SEXPTYPE> valid_types = {
    INTSXP, REALSXP, STRSXP, LGLSXP
  };
  
  if (!is_typeof(values, valid_types)) {
    stop("Invalid type for values vector");
  }
  
  if (!is_typeof(groups, valid_types)) {
    stop("Invalid type for groups vector");
  }

  return DISPATCH_GRP(_chisq_test, NumericVector(), values, groups);
}
