from elite.model import Model
from elite.stdlib.controls import FactorControl, NumericalControl
from elite.stdlib.metrics import ValueMetric, RatioMetric, DistributionMetric

# Controls

age_control = NumericalControl(
    name = 'Age',
    expression = 'Age',
    auto_breaks = False,
    breaks = [0,10,20,30,40,50,60,70,80,float('inf')],
)

income_control = NumericalControl(
    name = 'Income',
    expression = 'Total_Inc / 1000',
    auto_breaks = False,
    breaks = [0,5,10,20,30,40,50,60,70,80,100,120,140,180,200,250,300,
              float('inf')],
)

zip_control = FactorControl(
    name = 'Zip',
    expression = 'Anon_Zip',
)

# Metrics

refund_ratio_metric = RatioMetric(
    name = 'Refund_to_AGI',
    numerator = '-Refund_Bal',
    denominator = 'Adj_Gross_Inc',
    log_transform = True,
    cap_below = True,
    cap_below_at = 0,
    replace_zero = True,
    replace_zero_with = float('nan'),
    replace_inf = True,
    replace_inf_with = float('nan'),
    control_for = [income_control],
)

refund_exists_metric = ValueMetric(
    name = 'Has_Refund',
    expression = 'Refund_Bal < 0',
    control_for = [income_control],
)

med_ratio_metric = RatioMetric(
    name = 'Med_to_AGI',
    numerator = 'Tot_Med_Ded',
    denominator = 'Adj_Gross_Inc',
    cap_above = True,
    cap_above_at = 1.0,
    replace_zero = True,
    replace_zero_with = float('nan'),
    control_for = [age_control, income_control],
)

med_exists_metric = ValueMetric(
    name = 'Has_Med_Ded',
    expression = 'Tot_Med_Ded > 0',
    control_for = [age_control, income_control],
)

num_dependents_metric = ValueMetric(
    name = 'Num_Dependents',
    expression = 'Num_Depend',
    control_for = [age_control],
)

filing_stat_metric = DistributionMetric(
    name = 'Filing_Stat_Chisq',
    expression = 'FilingStat',
    kind = 'chi_square',
)

# Model

preparer_model = Model(
    entity_name = 'Anon_Entity_ID',
    group_name = 'Anon_Preparer_ID',

    controls = [
        age_control,
        income_control,
        zip_control,
    ],
    
    metrics = [
        refund_ratio_metric,
        refund_exists_metric,
        med_ratio_metric,
        med_exists_metric,
        num_dependents_metric,
        filing_stat_metric,
    ],
)