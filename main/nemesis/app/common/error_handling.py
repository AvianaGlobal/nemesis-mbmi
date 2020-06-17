""" Application error handling logic.
"""
from __future__ import absolute_import

import logging
import sys
import traceback

from traits.api import push_exception_handler
import enaml

from nemesis.ui.message_box import details_escape,critical, DialogButton

def init_error_handlers(debug = False):
    """ Initialize application error handlers.
    """
    # Configure logging.
    logging.basicConfig()
    logger = logging.getLogger('nemesis')
    logger.setLevel(logging.DEBUG if debug else logging.WARN)
    
    # Prevent Traits from suppressing errors.
    push_exception_handler(handler = lambda o, t, ov, nv: None,
                            reraise_exceptions = True,
                            main = True, locked = True)
    
    # Install GUI exception handler.
    if not debug:
        sys.excepthook = gui_except_hook


def gui_except_hook(exc_type, exc_value, exc_tb):
    """ Exception hook that displays error in a modal dialog.
    """
    logger = logging.getLogger('nemesis')
    logger.error('Uncaught exception', exc_info = (exc_type, exc_value, exc_tb))
    
    content = u'''\
An unexpected error has occurred. You are recommended to restart the application.
We apologize for the inconvenience.
        
If the error persists, please contact Aviana Global Technologies, Inc.'''
    exc_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    critical(text = 'Unexpected error', title = 'Error',
             content = content,
             details = details_escape(''.join(exc_lines)))