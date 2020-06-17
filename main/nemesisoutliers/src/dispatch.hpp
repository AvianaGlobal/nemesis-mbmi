// [[Rcpp::plugins(cpp11)]]

#include <Rcpp.h>
using namespace Rcpp;


/**
 * Checks if an R expression is one of the given types.
 */
inline bool is_typeof(SEXP exp, std::initializer_list<SEXPTYPE> types) {
  for (auto type : types) {
    if (TYPEOF(exp) == type) return true;
  }
  return false;
}

/**
 * A macro used to cast an Rcpp vector to a std::vector of a given type.
 */
#ifndef AS_VEC
#define AS_VEC(type, value) as< std::vector<type> >(value)
#endif

/**
 * A macro used to call a templated function with two type parameters for the
 * values and groups vectors.
 */
#ifndef _CALLF
#define _CALLF(f, t1, t2, values, groups, ...) \
  f<t1, t2>(AS_VEC(t1, values), AS_VEC(t2, groups), ##__VA_ARGS__)
#endif

/**
 * A macro used to dispatch a templated C++ function that performs a group
 * computation on a value and group vector. Currently supports dispatching
 * for INTSXP -> int, REALSXP -> double, STRSXP -> std::string, and
 * LGLSXP -> bool.
 * 
 * @param f The function to dispatch
 * @param failed The value returned if the column types are not matched
 * @param values An Rcpp vector of values
 * @param groups An Rcpp vector of the groups, corresponding to the values
 * @param ... The rest of the variadic arguments will be passed on to `f`
 */
#ifndef DISPATCH_GRP
#define DISPATCH_GRP(f, failed, values, groups, ...) (                        \
  TYPEOF(values) == INTSXP ?                                                  \
    TYPEOF(groups) == INTSXP ?                                                \
      _CALLF(f, int, int, values, groups, ##__VA_ARGS__)                      \
    : TYPEOF(groups) == REALSXP ?                                             \
      _CALLF(f, int, double, values, groups, ##__VA_ARGS__)                   \
    : TYPEOF(groups) == STRSXP ?                                              \
      _CALLF(f, int, std::string, values, groups, ##__VA_ARGS__)              \
    : TYPEOF(groups) == LGLSXP ?                                              \
      _CALLF(f, int, bool, values, groups, ##__VA_ARGS__)                     \
    : failed                                                                  \
  : TYPEOF(values) == REALSXP ?                                               \
    TYPEOF(groups) == INTSXP ?                                                \
      _CALLF(f, double, int, values, groups, ##__VA_ARGS__)                   \
    : TYPEOF(groups) == REALSXP ?                                             \
      _CALLF(f, double, double, values, groups, ##__VA_ARGS__)                \
    : TYPEOF(groups) == STRSXP ?                                              \
      _CALLF(f, double, std::string, values, groups, ##__VA_ARGS__)           \
    : TYPEOF(groups) == LGLSXP ?                                              \
      _CALLF(f, double, bool, values, groups, ##__VA_ARGS__)                  \
    : failed                                                                  \
  : TYPEOF(values) == STRSXP ?                                                \
    TYPEOF(groups) == INTSXP ?                                                \
      _CALLF(f, std::string, int, values, groups, ##__VA_ARGS__)              \
    : TYPEOF(groups) == REALSXP ?                                             \
      _CALLF(f, std::string, double, values, groups, ##__VA_ARGS__)           \
    : TYPEOF(groups) == STRSXP ?                                              \
      _CALLF(f, std::string, std::string, values, groups, ##__VA_ARGS__)      \
    : TYPEOF(groups) == LGLSXP ?                                              \
      _CALLF(f, std::string, bool, values, groups, ##__VA_ARGS__)             \
    : failed                                                                  \
  : TYPEOF(values) == LGLSXP ?                                                \
    TYPEOF(groups) == INTSXP ?                                                \
      _CALLF(f, bool, int, values, groups, ##__VA_ARGS__)                     \
    : TYPEOF(groups) == REALSXP ?                                             \
      _CALLF(f, bool, double, values, groups, ##__VA_ARGS__)                  \
    : TYPEOF(groups) == STRSXP ?                                              \
      _CALLF(f, bool, std::string, values, groups, ##__VA_ARGS__)             \
    : TYPEOF(groups) == LGLSXP ?                                              \
      _CALLF(f, bool, bool, values, groups, ##__VA_ARGS__)                    \
    : failed                                                                  \
  : failed                                                                    \
  )
#endif
