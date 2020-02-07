""" In this project, our fields always update "live", ala Traits UI.

This file defines convenience classes which have this behavior enabled by
default. All enaml Field imports should be made from here.
"""
from __future__ import absolute_import

import enaml
from atom.api import set_default
from enaml.widgets.api import Field as BaseField

with enaml.imports():
    from enaml.stdlib.fields import IntField as BaseIntField, \
        FloatField as BaseFloatField, RegexField as BaseRegexField


class Field(BaseField):
    
    submit_triggers = set_default(['lost_focus', 'return_pressed', 'auto_sync'])

class IntField(BaseIntField):
    
    submit_triggers = set_default(['lost_focus', 'return_pressed', 'auto_sync'])

class FloatField(BaseFloatField):
    
    submit_triggers = set_default(['lost_focus', 'return_pressed', 'auto_sync'])

class RegexField(BaseRegexField):
    
    submit_triggers = set_default(['lost_focus', 'return_pressed', 'auto_sync'])