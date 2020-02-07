def init_plot_config():
    """ Configure global plotting settings.
    """
    import matplotlib
    matplotlib.use('Qt4Agg')

    import seaborn
    seaborn.set_palette('deep')


def init_plot_editors():
    """ Register plot editors with their respective plots.
    """
    from elite.object_registry import ObjectFactory, ObjectRegistry

    import enaml
    with enaml.imports():
        from .plots.plot_editors import (ScatterPlotEditor, BarPlotEditor,
                                         HistogramPlotEditor, BoxPlotEditor)

    ObjectRegistry.instance().add(
        ObjectFactory(
            id = 'scatter_plot_editor',
            type = ScatterPlotEditor
        ),

        ObjectFactory(
            id = 'bar_plot_editor',
            type = BarPlotEditor
        ),

        ObjectFactory(
            id = 'histogram_plot_editor',
            type = HistogramPlotEditor
        ),

        ObjectFactory(
            id = 'box_plot_editor',
            type = BoxPlotEditor
        ),

        force=True
    )
