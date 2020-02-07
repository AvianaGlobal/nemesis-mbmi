from __future__ import absolute_import

import seaborn
from atom.api import Enum, observe, set_default

from .editable_plot import XYPlotSettings
from .matplotlib_widget import MatplotlibWidget


class BoxPlotSettings(XYPlotSettings):
    
    style = Enum('box', 'strip', 'violin')

    def copy(self):
        copied = super(BoxPlotSettings, self).copy()
        copied.style = self.style
        return copied


class BoxPlotWidget(MatplotlibWidget):
    
    # MatplotlibWidget interface
    
    multi_column = set_default(True)

    # The id of the editor widget in the ObjectRegistry
    editor_id = set_default('box_plot_editor')

    def _default_settings(self):
        return BoxPlotSettings()
    
    def _create_plot(self, figure):
        with seaborn.axes_style('whitegrid'):
            axes = figure.gca()
            plot_args = dict(
                x = 'variable', y = 'value',
                hue = self.group_by if self.group_by else None,
                data = self._create_plot_data(melt=True),
                orient = 'v',
                ax = axes,
            )
            if self.settings.style == 'box':
                seaborn.boxplot(sym='', width=0.5, **plot_args)
            elif self.settings.style == 'strip':
                seaborn.stripplot(jitter=True, **plot_args)
            elif self.settings.style == 'violin':
                seaborn.violinplot(**plot_args)
            axes.legend(loc=1) # upper right, not automatic
            axes.set_xlabel('')
            axes.set_ylabel('')
            return axes

    @observe('settings', 'settings.style')
    def _update_figure(self, change):
        if change['type'] == 'update':
            self.reload_figure()
