from __future__ import absolute_import

from collections import OrderedDict

import numpy as np
from matplotlib import pyplot as plt
import seaborn

from atom.api import Bool, Enum, Signal, Typed, Unicode, observe, set_default
from enaml.core.api import d_

from nemesis.data.heuristics import is_discrete
from nemesis.ui.message_box import question
from .editable_plot import XYPlotSettings
from .histogram import auto_bin
from .matplotlib_widget import MatplotlibWidget


class HistogramPlotSettings(XYPlotSettings):
    # The method to use for binning the data. See ``auto_histogram()``.
    bin_method = Enum('fd', 'rice', 'sqrt', 'sturges', 'custom')

    # The number of bins to use. Can be set automatically by a heuristic
    # (`bin_method`) or set manually (when `bin_method == 'custom'`).
    bins = Typed(OrderedDict)

    # A signal emitted when a bin number is changed.
    bins_changed = Signal()

    # Whether to show the usual histogram, a smoothed kernel density estimate,
    # and a "rug" plot on the x-axis, respectively.
    show_hist = Bool(True)
    show_kde = Bool(False)
    show_rug = Bool(False)

    def set_bins(self, group_name, bins):
        """ Set the number of bins for a group. This method must be used
        instead of directly modifying the dictionary, as Atom doesn't
        currently support container notifications for dictionaries.
        """
        if self.bins.get(group_name) != bins:
            self.bins[group_name] = bins
            self.bins_changed.emit()

    def trim_bins(self, valid_group_names):
        """ Remove all bin keys that are not in valid_group_names.
        """
        for key in self.bins:
            if key not in valid_group_names:
                del self.bins[key]

    def copy(self):
        copied = super(HistogramPlotSettings, self).copy()

        copied.bin_method = self.bin_method
        copied.bins = self.bins.copy()
        copied.show_hist = self.show_hist
        copied.show_kde = self.show_kde
        copied.show_rug = self.show_rug

        return copied


class HistogramWidget(MatplotlibWidget):
    """ An Enaml widget for displaying group and population histograms
    side-by-side.
    """

    # Label for y-axis.
    y_label = d_(Unicode('Density'))

    # The id of the editor widget in the ObjectRegistry
    editor_id = set_default('histogram_plot_editor')

    def _default_settings(self):
        settings = HistogramPlotSettings()
        settings.bins = self._calculate_bins(settings.bin_method)
        return settings
    
    # MatplotlibWidget interface

    def _create_plot(self, figure):
        col_name = self.data_columns[0] # (multi_column = False)
        df = self._create_plot_data()
        s = self.settings

        grouped = self._group_data(df)
        s.trim_bins(map(lambda g: g[0], grouped))
        pop_range = (df[col_name].min(), df[col_name].max())

        with seaborn.axes_style('whitegrid'):
            layout = self._plot_layout(len(grouped))
            pal = seaborn.color_palette('Purples_r')

            axis = None
            for i, (group_name, group) in enumerate(grouped):
                axis = plt.subplot(layout[0], layout[1], i + 1, sharex=axis, sharey=axis)
                axis.grid(True)
                seaborn.despine(figure, axis, right=False)

                hist_kws = dict(normed=True, range=pop_range)
                kde_kws = dict(cut=np.inf, clip=pop_range)
                seaborn.distplot(group[col_name].dropna(),
                    hist=s.show_hist, kde=s.show_kde, rug=s.show_rug,
                    bins=self._get_bins(group_name, group[col_name]),
                    hist_kws=hist_kws, kde_kws=kde_kws, norm_hist=True, ax=axis,
                    color=pal[i % len(pal)])

                if i % layout[1] == 0:
                    axis.set_ylabel(self.y_label)

                axis.set_title(group_name)
                axis.set_xlabel(col_name)
                axis.set_xlim(pop_range)

            return figure.gca()

    def validate_drop(self, data_frame, columns):
        data = data_frame[columns[0]]
        ok = True
        if is_discrete(data):
            msg = 'The selected data does not appear to be continuous. '\
                'Are you sure you wish to continue?'
            button = question(parent=self, title='Continue?',
                              text='Possibly incorrect data type', content=msg)
            ok = button and button.action == 'accept'
        return ok
            
    # Private interface.

    def _get_bins(self, group_name, data):
        s = self.settings

        if group_name not in s.bins:
            s.set_bins(group_name, self._bin_group(data, s.bin_method))

        return s.bins[group_name]

    def _group_data(self, df):
        if self.group_by:
             return df.groupby(self.group_by, sort=False)
        return [('', df)]

    def _calculate_bins(self, bin_method):
        grouped = self._group_data(self._create_plot_data())
        col_name = self.data_columns[0]

        return OrderedDict([
            (name, self._bin_group(group[col_name], bin_method))
            for name, group in grouped
        ])

    def _bin_group(self, group, bin_method):
        if bin_method == 'custom':
            # This is an ambiguous case, arbitrarily default to a method
            bin_method = 'fd'

        return auto_bin(group, method=bin_method)

    @observe('settings.bin_method')
    def _bin_method_changed(self, change):
        method = change['value']
        if method != 'custom':
            self.settings.bins = self._calculate_bins(method)

    @observe('settings', 'settings.bins', 'settings.show_hist',
             'settings.show_kde', 'settings.show_rug')
    def _update_figure(self, change):
        if change['type'] == 'update':
            self.reload_figure()

    @observe('settings.bins_changed')
    def _bins_changed_fired(self):
        self.reload_figure()
