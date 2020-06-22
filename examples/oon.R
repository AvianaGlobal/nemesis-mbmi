library(NemesisOutliers)

# Configure model

def_parameters(entity_name = 'CONSUMER_ID',
               group_name = 'CLIENT_ID',
               cap_entity_score = 3.0,
               min_group_size = 50)

# Control variables

def_control(sex = CONSUMER_GENDER_CD)

def_control(age = cut(AGE_AT_CVG_START,
                breaks = 10,
                right = FALSE))

# Metrics

def_metric(claims = PRIOR_CLM_CNT,
           control_for = c('sex', 'age'))

def_metric(zipclaimrate = ratio(ZIP_CLAIM_CNT, ZIP_CONSUMER_CNT))

def_group_metric('uids',
                 CONSUMER_ID,
                 uniq_disc,
                 type = 'distinct')

def_group_metric('member_density',
                 MEMBERSHIP_PARTICIPATION_KEY,
                 graph_density)

# Composite scores

def_composite_score(score = 1.0 * claims + 2.0 * zipclaimrate + 1.0 * uids + 1.0 * member_density)

# Execute model

run_model(ConnStr = 'DRIVER={IBM DB2 ODBC DRIVER}; DATABASE=BLUDB;HOSTNAME=dashdb-txn-sbox-yp-dal09-03.services.dal.bluemix.net;PORT=50000;PROTOCOL=TCPIP;UID=kfn42270;PWD=6kg39fqcqk+tqqpf',
          input_table = 'select * from "input" where CONSUMER_GENDER_CD = \'F\'',
          db2 = 1)