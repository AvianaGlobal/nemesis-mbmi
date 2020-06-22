library(NemesisOutliers)
library(DBI)
library(RSQLite)

# Configure model

def_parameters(entity_name = 'UNIQUE_CLM_ID',
               group_name = 'DR_TAX_ID',
               cap_entity_score = 3.0,
               min_group_size = 50)

# Control variables

def_control(sex = PAT_SEX_CD)

def_control(age = cut(PAT_AGE,
                breaks = 10,
                right = FALSE))

# Metrics

def_metric(amt = CLM_DRPD_AMT,
           control_for = c('sex', 'age'))

def_metric(ratio = ratio(CLM_DRPD_AMT, CLAIM_COMPONENTS))

def_group_metric('uids',
                 CONSUMER_ID,
                 uniq_disc,
                 type = 'distinct')

# Composite scores

def_composite_score_q('pca', composite.pca, top = 1.0, percent = TRUE)

def_composite_score(score = 1.0 * amt + 2.0 * ratio + 1.0 * state + 3.0 * uids)

# Execute model

run_model(input = 'C:/Users/MichaelJohnson/install_test/nemesis-mbmi/examples/vsp.csv',
          output = dbConnect(dbDriver('SQLite'), dbname = 'C:/Users/MichaelJohnson/install_test/nemesis-mbmi/examples/vsp.db'),
          store_input = TRUE)