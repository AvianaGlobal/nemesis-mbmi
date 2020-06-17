""" This module simply re-implements the convenvience functions in 
``enaml.stdlib.message_box`` to provide more options.
"""
from __future__ import absolute_import

import enaml

with enaml.imports():
    from enaml.stdlib.message_box import MessageBox, DialogButton, \
        _ICONS as MESSAGE_ICONS


def details_escape(s):
    """ Escape a raw text string for display in the details section of a 
    MessageBox.
    """
    from cgi import escape
    return escape(s)


def critical(**kwds):
    return _exec_box(image = MESSAGE_ICONS['critical'](), **kwds)

def information(**kwds):
    return _exec_box(image = MESSAGE_ICONS['information'](), **kwds)

def question(**kwds):
    if 'buttons' not in kwds:
        kwds['buttons'] = [ DialogButton('Yes', 'accept'),
                            DialogButton('No', 'reject'), ]
    return _exec_box(image = MESSAGE_ICONS['question'](), **kwds)

def warning(**kwds):
    return _exec_box(image = MESSAGE_ICONS['warning'](), **kwds)


def _exec_box(**kwds):
    buttons = kwds.setdefault('buttons', [])
    if not buttons:
        buttons.append(DialogButton('OK', 'accept'))
    
    box = MessageBox(**kwds)
    box.exec_()
    for button in box.buttons:
        if button.was_clicked:
            return button