library(EliteOutliers)
library(RSQLite)

# Configure model

def_parameters(entity_name = 'Anon_Entity_ID',
               group_name = 'Anon_Preparer_ID',
               cap_entity_score = 3.0,
               min_group_size = 50)

# Control variables

def_control(age = cut(Age,
                breaks = c(0, 10, 20, 30, 40, 50, 60, 70, 80, Inf),
                right = FALSE))

def_control(income = cut(Total_Inc,
                breaks = c(0, 5000, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 80000, 100000, 120000, 140000, 180000, 200000, 250000, 300000, Inf),
                labels = c('a-5k', 'b-10k', 'c-20k', 'd-30k', 'e-40k', 'f-50k', 'g-60k', 'h-70k', 'g-80k', 'j-100k', 'k-120k', 'l-140k', 'm-180k', 'n-200k', 'o-250k', 'p-300k', 'q-300+'),
                right = FALSE))

# Metrics

def_metric(med_to_AGI = ratio(Tot_Med_Ded, Adj_Gross_Inc, max = 1.0),
           control_for = c('age', 'income'))

def_metric(med_to_inc = ratio(Tot_Med_Ded, Total_Inc, max = 1.0),
           control_for = c('age', 'income'))

def_metric(has_med_ded = Tot_Med_Ded > 0,
           control_for = c('age', 'income'))

# Composite scores

def_composite_score(score = 0.5 * med_to_inc + 0.5 * has_med_ded)

# Execute model

run_model(input = 'Anon_Prep_Data.csv',
          output = dbConnect(dbDriver('SQLite'), dbname = 'results.db'),
          store_input = TRUE)