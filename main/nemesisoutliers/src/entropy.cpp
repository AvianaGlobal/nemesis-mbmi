// [[Rcpp::plugins(cpp11)]]

#include <Rcpp.h>
#include "counts.hpp"
#include "dispatch.hpp"
using namespace Rcpp;
static const int mqDEBUG = 0;

//' @name  _entropy_disc
//' @rdname entropy_disc
template <typename T, typename U>
NumericVector _entropy_disc (std::vector<T> values, std::vector<U> groups, std::string type) {
  if (type != "frequent" && type != "normal" && type != "dump") {
	stop("Unknown entropy_disc type: " + type);
  }
  auto c = counts( values, groups);
  auto group_counts = c.second;
  int i = 0;
  if (mqDEBUG == 1 || type == "dump") {
	auto popFreq = c.first;
	const int gn = popFreq.size();
	NumericVector out(gn);
	GenericVector names(gn);
	for (auto pair : popFreq) {
		out[i] = pair.second;
		names[i] = pair.first;
		++i;
	}
	out.attr("names") = names;
	return out;
  }
  const int gn = group_counts.size();
  NumericVector out(gn);
  GenericVector names(gn);
  if (mqDEBUG == 2) {
    for (auto g : group_counts) {
		auto groupFreq = g.second;
	    for (auto pair : groupFreq) {
			out[i] = pair.second;
//			std::string ss << g.first << '_' << pair.first;
//			std::string gg = std::to_string( g.first);
//			std::string pp = std::to_string( pair.first);
//			names[i] = gg + pp;   // g.first + pair.first;
			names[i] = g.first;
			++i;
		}
	}
	out.attr("names") = names;
	return out;
  }
  for (auto pair : group_counts) {
    auto grp = pair.second;
    const auto grp_size = group_size(grp);
	double entr= 0;
	for (auto cats : grp) {
	  double prob = cats.second;		// frequency
	  if (prob > 0) {
	    prob /= (double)grp_size;		// relative frequency = probability
	    prob *= -log(prob);
	    if (type == "normal") prob /= log(grp_size);
	  }
	  entr += prob;
	}
    out[i] = entr;
    names[i] = pair.first;
    i++;
  }
  out.attr("names") = names;
  return out;
}

//' Compute information entropy of the values in each group.
//'
//' @param \code{values} The vector of values
//' @param \code{groups} The vector of groups, corresponding to the values
//' @param \code{type} The type of ratio to compute: "normal" or "frequent"
//'
//' @return A numeric vector of the values for each group, named by group.
//' Entropy is maximal when all events are equaly probable.
//' Normalized entropy is also known as Efficiency. It is the computed entropy
//'    divided by the maximum possible entropy for N events = log(N)
//' See, eg, https://en.wikipedia.org/wiki/Entropy_(information_theory)
//' @export
// [[Rcpp::export]]
NumericVector entropy_disc(SEXP values, SEXP groups, std::string type) {
  std::initializer_list<SEXPTYPE> valid_types = {
    INTSXP, REALSXP, STRSXP, LGLSXP
  };
  if (!is_typeof(values, valid_types)) {
    stop("Invalid type for values vector");
  }
  if (!is_typeof(groups, valid_types)) {
    stop("Invalid type for groups vector");
  }
  return DISPATCH_GRP(_entropy_disc, NumericVector(), values, groups, type);
}
