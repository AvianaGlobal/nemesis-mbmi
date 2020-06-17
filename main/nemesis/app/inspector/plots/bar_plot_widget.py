from __future__ import absolute_import

import seaborn
import pandas as pd
from atom.api import Bool, Enum, Unicode, observe, set_default
from enaml.core.api import d_

from nemesis.data.heuristics import is_discrete
from nemesis.ui.message_box import question
from nemesis.app.inspector.plots.editable_plot import XYPlotSettings
from nemesis.app.inspector.plots.matplotlib_widget import MatplotlibWidget


def float_str(x, low_threshold=1e-4, high_threshold=1e4):
    """ Convert a float number to a string in its most compact form.
    """
    # Integers don't need trailing .0
    if int(x) == x:
        return str(int(x))

    # If the number is very low or very high, use scientific notation
    if x <= low_threshold or x >= high_threshold:
        return '%.2E' % x

    # Show a maximum of 4 decimal places
    return '%.4f' % x


def autolabel(rects, ax):
    """ Label a list of matplotlib Rectangles with their height.
    See http://matplotlib.org/examples/api/barchart_demo.html.
    """
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2.,
                height + 1e-5, float_str(height), ha='center',
                va='bottom')


class BarPlotSettings(XYPlotSettings):
    
    style = Enum('separate', 'together')

    show_labels = Bool(True)

    def copy(self):
        copied = super(BarPlotSettings, self).copy()
        copied.style = self.style
        copied.show_labels = self.show_labels
        return copied


class BarPlotWidget(MatplotlibWidget):
    """ An Enaml widget for displaying group and population bar graphs
    side-by-side.
    """
    
    # Label for y-axis.
    y_label = d_(Unicode('Probability'))

    # The id of the editor widget in the ObjectRegistry
    editor_id = set_default('bar_plot_editor')
    
    # MatlotlibWidget interface.
    
    def _default_settings(self):
        return BarPlotSettings()
    
    def _create_plot(self, figure):
        col_name = self.data_columns[0] # (multi_column = False)

        # Create data frame of relative frequencies.
        df = self._create_plot_data()
        proportions = lambda df:\
            df[col_name].value_counts(normalize=True, sort=False)
        if self.group_by:
            grouped = df.groupby(self.group_by, sort=False)
            props = grouped.apply(proportions)
            df = props.reset_index()
            if isinstance(props, pd.Series):
                df.columns = [ self.group_by, col_name, 'p' ]
            else:
                df = pd.melt(df, id_vars=[self.group_by], var_name=col_name, value_name='p')
        else:
            df = proportions(df).reset_index()
            df.columns = [ col_name, 'p' ]
        # Create plot(s).
        with seaborn.axes_style('white'):
            axes = figure.gca()
            
            if self.settings.style == 'together':
                group = self.group_by if self.group_by else None
                seaborn.barplot(x=col_name, y='p', hue=group, data=df, ax=axes,
                                ci=None)
                axes.legend(loc=1) # upper right, not automatic
                axes.set_ylabel(self.y_label)
            
            elif self.settings.style == 'separate':
                if self.group_by:
                    plot_df = df.pivot(col_name, self.group_by)['p']
                    # XXX: Preserve group order lost by pivot.
                    plot_df = plot_df[df[self.group_by].unique()]
                else:
                    plot_df = df.set_index(col_name)
                sub_axes = plot_df.plot(kind='bar', ax=axes, subplots=True,
                    layout=self._plot_layout(len(plot_df.columns)),
                    sharex=False, sharey=False, fontsize=10, legend=False, rot=0)

                for i in range(len(sub_axes)):
                    row = sub_axes[i]
                    for j in range(len(row)):
                        if self.settings.show_labels:
                                autolabel(row[j].patches, row[j])

                        # Set the y label of the first plot in every row of the subplots
                        if j == 0:
                            row[j].set_ylabel(self.y_label)
                        else:
                            row[j].set_ylabel('')

            return axes

    def validate_drop(self, data_frame, columns):
        data = data_frame[columns[0]]
        ok = True
        if not is_discrete(data):
            msg = 'The selected data does not appear to be discrete. '\
                'Are you sure you wish to continue?'
            button = question(parent=self, title='Continue?',
                              text='Possibly incorrect data type', content=msg)
            ok = button and button.action == 'accept'
        return ok
    
    @observe('settings', 'settings.style', 'settings.show_labels')
    def _update_figure(self, change):
        if change['type'] == 'update':
            self.reload_figure()