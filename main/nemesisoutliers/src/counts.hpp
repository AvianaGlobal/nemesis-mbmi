// [[Rcpp::plugins(cpp11)]]

//' Compute the size of a group from its counts.
//' 
//' @name group_size
//' 
//' @param \code{group} A map from the counts of the group
//' 
//' @return The size of the group
template <typename T>
int group_size(std::map<T, int> &group) {
  return std::accumulate(group.begin(), group.end(), 0, [](int acc, std::pair<T, int> p) {
    return acc + p.second;
  });
}

//' Find the largest count in a group.
//' 
//' @name max_group_count
//' 
//' @param \code{group} A map from the counts of the group
//' 
//' @return The size of the group
template <typename T>
int max_group_count(std::map<T, int> &group) {
  typename std::map<T, int>::iterator it;
  it = std::max_element(group.begin(), group.end(), [](std::pair<T, int> a, std::pair<T, int> b) {
    return a.second < b.second;
  });
  
  if (it == group.end()) return -1;
  return it->second;
}

//' Compute the population and group counts for a vector of values and
//' corresponding vector of group identifiers.
//' 
//' @name counts
//' 
//' @param \code{values} The vector of values
//' @param \code{groups} The vector of groups, corresponding to the values
//' 
//' @return A std::pair where the first item is the map of value -> count for the population,
//' and the second item is the map of group -> value -> count for the groups.
template <typename T, typename U>
std::pair< std::map<T, int>, std::map< U, std::map<T, int> > >
counts(std::vector<T> &value_col, std::vector<U> &group_col) {
  std::map<T, int> pop;
  std::map< U, std::map<T, int> > groups;
  int n, i;
  
  n = value_col.size();
  
  for (i = 0; i < n; i++) {
    auto &group = groups[group_col[i]];
    auto value = value_col[i];
    int c;
    
    c = pop[value];
    pop[value] = c + 1;
    
    c = group[value];
    group[value] = c + 1;
  }
  
  return std::make_pair(pop, groups);
}

template <typename T>
std::map<T, int> count_unique(std::vector<T> &values) {
  std::map<T, int> cnts;
  
  for (auto v : values) {
    cnts[v]++;
  }
  
  return cnts;
}