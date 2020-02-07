context("stat_util")

test_that("ks.stat works with continuous data", {
  repeat {
    x <- runif(100)
    y <- runif(100)
    if (length(unique(c(x,y))) == 200) break
  }
  actual <- ks.stat(x, y)
  target <- ks.test(x, y)$statistic
  expect_that(actual, is_equivalent_to(target))
})