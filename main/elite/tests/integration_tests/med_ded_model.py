from elite.model import Model
from elite.stdlib.controls import NumericalControl
from elite.stdlib.metrics import ValueMetric, RatioMetric
from elite.stdlib.composite_scores import LinearCombinationScore, LinearTerm


controls = [
    NumericalControl(
        name = 'age',
        expression = 'Age',
        auto_breaks = False,
        breaks = [0,10,20,30,40,50,60,70,80,float('inf')]),

    NumericalControl(
        name = 'income',
        expression = 'Total_Inc',
        auto_breaks = False,
        breaks = [x * 1000 for x in
                  [0,5,10,20,30,40,50,60,70,80,100,120,140,180,200,250,300,
                   float('inf')]],
        labels = ['a-5k','b-10k','c-20k','d-30k','e-40k','f-50k','g-60k',
                  'h-70k','g-80k','j-100k','k-120k','l-140k','m-180k',
                  'n-200k','o-250k','p-300k','q-300+']),
]

metrics = [
    RatioMetric(
        name = 'med_to_AGI',
        numerator = 'Tot_Med_Ded',
        denominator = 'Adj_Gross_Inc',
        cap_above = True,
        control_for = controls),

    RatioMetric(
        name = 'med_to_inc',
        numerator = 'Tot_Med_Ded',
        denominator = 'Total_Inc',
        cap_above = True,
        control_for = controls),

    ValueMetric(
        name = 'has_med_ded',
        expression = 'Tot_Med_Ded > 0',
        control_for = controls),
]

composite_scores = [
    LinearCombinationScore(
        name = 'score',
        terms = [ LinearTerm(metric=metrics[1], coeff=0.5),
                  LinearTerm(metric=metrics[2], coeff=0.5) ]),
]

med_ded_model = Model(
    entity_name = 'Anon_Entity_ID',
    group_name = 'Anon_Preparer_ID',
    limit_group_size = True,

    controls = controls,
    metrics = metrics,
    composite_scores = composite_scores,
)