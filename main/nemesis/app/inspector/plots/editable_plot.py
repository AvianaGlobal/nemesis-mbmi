from __future__ import absolute_import

from atom.api import Atom, Typed, Unicode, Signal, observe
from enaml.core.api import d_

from nemesis.app.inspector.plots.plot_limits import PlotLimits


class PlotSettings(Atom):
    """ The base class for all plot settings instances.

    """
    # The title for the plot
    title = Unicode()

    settings_changed = Signal()

    def _observe_title(self, change):
        if change['type'] == 'update':
            self.settings_changed.emit()

    def copy(self):
        return self.__class__(title=self.title)


class XYPlotSettings(PlotSettings):
    """ A PlotSettings class that includes PlotLimits instances for the X and Y
    axes.
    """
    x_limits = Typed(PlotLimits)
    y_limits = Typed(PlotLimits)

    @observe('x_limits', 'x_limits.low', 'x_limits.high',
             'y_limits', 'y_limits.low', 'y_limits.high')
    def _limits_changed(self, change):
        if change['type'] == 'update':
            self.settings_changed.emit()

    def copy(self):
        copied = super(XYPlotSettings, self).copy()
        copied.x_limits = PlotLimits.from_tuple(self.x_limits.as_tuple())
        copied.y_limits = PlotLimits.from_tuple(self.y_limits.as_tuple())
        return copied


class EditablePlot(Atom):
    """ A base class for editable plots, providing basic editor setup as well
    as plot default restoration support.
    """

    # The id of the editor widget in the ObjectRegistry
    editor_id = Unicode()

    # The settings instance for the plot
    settings = d_(Typed(PlotSettings))

    # Internal state
    _saved_settings = Typed(PlotSettings)

    def can_edit(self):
        """ Returns whether the plot is currently editable.
        """
        return True

    def update_from_settings(self):
        """ Update the plot from the current settings object.
        """

    def save_settings(self, force=False):
        """ Save the current settings instance. By default, this won't
        override an already saved settings instance. This behavior can be
        changed with the `force` flag.
        """
        if self._saved_settings is None or force:
            self._saved_settings = self.settings.copy()

    def restore_settings(self):
        """ Restore the saved settings instance.
        """
        if self._saved_settings is not None:
            self.settings = self._saved_settings
            self._saved_settings = self._saved_settings.copy()

    def clear_settings(self):
        """ Clear the currently saved settings.
        """
        self._saved_settings = None

    def _observe_settings(self, change):
        old = change.get('oldvalue')
        if old is not None:
            old.unobserve('settings_changed', self.update_from_settings)

        new = change['value']
        new.observe('settings_changed', self.update_from_settings)

        if change['type'] == 'update':
            self.update_from_settings()
