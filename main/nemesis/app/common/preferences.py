from __future__ import absolute_import

import json
import os

from traits.api import HasTraits, Property, Enum, File, Dict

from nemesis.app.common.etsconfig import ETSConfig


# Preferences kind constants
BUILDER = 'builder'
INSPECTOR = 'inspector'

# Preferences defaults
DEFAULTS = {
    BUILDER: {},
    INSPECTOR: {
        'sample_data_threshold': 100000,
        'sample_pop': True,
        'sample_pop_size': 10**4,
    }
}


class Preferences(HasTraits):
    """ An object used to manage the application preferences. A preferences
    instance is created with a kind that is used to determine which preferences
    to load. This generalizes the preferences to be usable for both the builder
    and inspector.
    """
    kind = Enum(BUILDER, INSPECTOR)
    path = Property(File, depends_on='kind')

    _prefs = Dict
    _instances = {}

    @classmethod
    def instance(cls, kind):
        if kind not in cls._instances:
            cls._instances[kind] = cls(kind)
        return cls._instances[kind]

    def __init__(self, kind, *args, **kwargs):
        super(Preferences, self).__init__(*args, **kwargs)
        self.kind = kind

    def _get_path(self):
        home = ETSConfig.application_data
        if not os.path.exists(home):
            os.mkdir(home)
        return os.path.join(home, 'preferences_%s.json' % self.kind)

    def _kind_changed(self, new):
        prefs = DEFAULTS[new].copy()

        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                prefs.update(json.load(f))

        self._prefs = prefs

    def get(self, option):
        return self._prefs[option]

    def set(self, option, value):
        self._prefs[option] = value

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self._prefs, f)
