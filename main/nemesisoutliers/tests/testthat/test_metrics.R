library(data.table, warn.conflicts = FALSE)

context("metrics")

test_that("ratio metric works", {
  x <- c(1,0,1,NA)
  y <- c(2,1,0,1)
  expect_that(ratio(x, y), equals(c(0.5,0,Inf,NA)))
  expect_that(ratio(x, y, zero_to=1, inf_to=2, na_to=3), equals(c(0.5,1,2,3)))
  expect_that(ratio(x, y, max=1), equals(c(0.5,0,1,NA)))
  expect_that(ratio(x, y, max=1, max_to=2), equals(c(0.5,0,2,NA)))
})

test_that("chi squared metric works", {
  x <- c(1, 1, 2, 2)
  y <- c(1, 2, 3, 3)
  value <- 100 * (1 - pchisq(2, 2, lower.tail = FALSE))
  expected <- c(value, value)
  names(expected) <- c(1, 2)
  
  expect_that(chisq_test(y, x), equals(expected))
})

test_that("unique discrete metric works", {
  x <- c(1, 1, 1, 2, 2)
  y <- c(1, 2, 2, 3, 3)
  
  expected_distinct <- c(0.5, 0)
  names(expected_distinct) <- c(1, 2)
  expect_that(uniq_disc(y, x, "distinct"), equals(expected_distinct))
  
  expected_frequent <- c(2/3, 1)
  names(expected_frequent) <- c(1, 2)
  expect_that(uniq_disc(y, x, "frequent"), equals(expected_frequent))
})

test_that("unique continuous metric works", {
  x <- c(1, 1, 1, 2, 2, 3)
  y <- c(1, 5, 2, 4, 3, 6)
  
  cov <- function(a) sd(a) / mean(a)
  expected <- c(cov(c(1, 5, 2)) / cov(y), cov(c(4, 3)) / cov(y), cov(c(6)) / cov(y))
  names(expected) <- c(1, 2, 3)
  
  expect_that(uniq_cont(y, x), equals(expected))
})

test_that("graph density metric works", {
  x <- c(1, 1, 1, 1, 2, 2, 2, 2, 3, 3)
  y <- c(1, 2, 2, 2, 1, 2, 1, 2, 1, 2)
  
  expected <- c(1/2, 1/3, 0)
  names(expected) <- c(1, 2, 3)
  
  expect_that(graph_density(y, x), equals(expected))
})

test_that("discrete entropy metric works", {
  groupID <- c(1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3)
  catValu <- c('A', 'C', 'B', 'D', 'D', 'D', 'D', 'D', 'D', 'D', 'A', 'A',
               'C', 'C', 'C', 'E', 'E', 'A', 'A', 'A', 'A', 'D', 'D', 'D', 'A')
 
  expected <- c(0.940447989, 1.082195530, 0.682908105)
  names(expected) <- c(1, 2, 3)
  
  expect_that(entropy_disc( catValu, groupID, 'frequent'), equals(expected))
})