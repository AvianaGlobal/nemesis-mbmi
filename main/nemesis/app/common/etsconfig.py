""" ETS config importer.

Ensures that the ETS application directories are properly configured.
"""
from __future__ import absolute_import

from traits.etsconfig.api import ETSConfig


# Use hyphen because this string is used in file names.
ETSConfig.company = 'AvianaGlobal'