def init_stdlib():
    """ Register all the standard model components.
    """
    from ..object_registry import ObjectFactory, ObjectRegistry

    from .controls import FactorControl, NumericalControl
    from .metrics import ValueMetric, RatioMetric, DistributionMetric, \
		EntropyMetric, \
        UniqueDiscreteMetric, UniqueContinuousMetric, GraphDensityMetric
    from .composite_scores import LinearCombinationScore, CustomScore, \
        PrincipalComponentScore

    import traits_enaml
    with traits_enaml.imports():
        from .ui.controls import FactorControlView, NumericalControlView
        from .ui.metrics import ValueMetricView, EntropyMetricView, RatioMetricView, \
            DistributionMetricView, UniqueDiscreteMetricView, \
            UniqueContinuousMetricView, GraphDensityMetricView
        from .ui.composite_scores import LinearCombinationScoreView, \
            CustomScoreView, PrincipalComponentScoreView

    ObjectRegistry.instance().add(
        # Controls
        ObjectFactory(
            id = 'factor_control',
            name = 'Categorical',
            description = 'Control for a categorical variable',
            type = FactorControl,
            ui = FactorControlView,
        ),
        ObjectFactory(
            id = 'numerical_control',
            name = 'Numerical',
            description = 'Control for a numerical variable',
            type = NumericalControl,
            ui = NumericalControlView,
        ),

        # Metrics
        ObjectFactory(
            id = 'value_metric',
            name = 'Simple value',
            description = 'Compute a simple expression (boolean or numerical)',
            type = ValueMetric,
            ui = ValueMetricView,
        ),
        ObjectFactory(
            id = 'entropy_metric',
            name = 'Entropy',
            description = 'Compute entropy of groups',
            type = EntropyMetric,
            ui = EntropyMetricView,
		),
         ObjectFactory(
            id = 'ratio_metric',
            name = 'Ratio',
            description = 'Compute the ratio between two numerical values',
            type = RatioMetric,
            ui = RatioMetricView,
        ),
        ObjectFactory(
            id = 'distribution_metric',
            name = 'Statistic',
            description = 'Compute statistics of the group and population data',
            type = DistributionMetric,
            ui = DistributionMetricView,
        ),
        ObjectFactory(
            id='unique_discrete_metric',
            name='Unique (Discrete)',
            description='Compute the ratio of unique values in each group',
            type=UniqueDiscreteMetric,
            ui=UniqueDiscreteMetricView
        ),
        ObjectFactory(
            id = 'unique_continuous_metric',
            name='Unique (Continuous)',
            description='Compute the ratio of coefficients of variance in each group',
            type=UniqueContinuousMetric,
            ui=UniqueContinuousMetricView
        ),
        ObjectFactory(
            id = 'graph_density_metric',
            name='Graph Density',
            description='Compute the density of the links between values within each group',
            type=GraphDensityMetric,
            ui=GraphDensityMetricView
        ),

        # Composite scores
        ObjectFactory(
            id = 'linear_combination_score',
            name = 'Simple linear combination',
            description = 'A manually specified linear combination',
            type = LinearCombinationScore,
            ui = LinearCombinationScoreView,
        ),
        ObjectFactory(
            id = 'custom_score',
            name = 'Custom score',
            description = 'A score computed by an arbitrary expression',
            type = CustomScore,
            ui = CustomScoreView,
        ),
        ObjectFactory(
            id = 'principal_component_score',
            name = 'Principal component analysis',
            description = 'A composite score using principal component analysis',
            type = PrincipalComponentScore,
            ui = PrincipalComponentScoreView
        )
    )
