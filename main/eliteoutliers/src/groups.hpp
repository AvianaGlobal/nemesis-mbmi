// [[Rcpp::plugins(cpp11)]]

//' Group a vector of values, using a corresponding group vector.
//' 
//' @name group
//' 
//' @param \code{value_col} The vector of values
//' @param \code{group_col} The vector of groups, corresponding to the values
//' 
//' @return A map from group -> vector of values
template <typename T, typename U>
std::map< U, std::vector<T> >
group(std::vector<T> &value_col, std::vector<U> &group_col) {
  std::map< U, std::vector<T> > groups;
  const int n = value_col.size();
  for (int i = 0; i < n; i++) {
    auto &group = groups[group_col[i]];
    auto value = value_col[i];
    group.push_back(value);
  }
  return groups;
}