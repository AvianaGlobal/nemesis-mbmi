""" An Enaml toolbar with some additional features.
"""
from __future__ import absolute_import

import sys

from atom.api import Unicode
from enaml.core.declarative import d_
from enaml.qt import QtCore
from enaml.widgets.api import ToolBar as BaseToolBar


class ToolBar(BaseToolBar):
    
    # The title displayed by the toolbar context menu.
    title = d_(Unicode())
    
    # ToolkitObject interface
    
    def activate_proxy(self):
        super(ToolBar, self).activate_proxy()
        
        widget = self.proxy.widget
        widget.setWindowTitle(self.title)
        
        # XXX: Work around Qt bug on Retina displays. To prevent toolbars being
        # twice the correct size, set the toolbar size manually.
        if sys.platform == 'darwin':
            widget.setIconSize(QtCore.QSize(32, 32))
