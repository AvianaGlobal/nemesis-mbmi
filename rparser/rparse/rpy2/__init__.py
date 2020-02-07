""" An rpy2 importer with improved directory detection logic.

All rpy2 imports should be made from this package, not the system rpy2!
"""
from __future__ import absolute_import

import ctypes
import os

import logging
logger = logging.getLogger(__name__)


def putenv(name, value):
    """ Set an environment variable at both the Python and C levels.

    This is necessary because rpy2 reads the environment using C calls and
    Python does not write to the environment at this level:

        http://bugs.python.org/issue16633
    """
    os.environ[name] = value
    if os.name == 'nt':
        msvcrt = ctypes.cdll.msvcrt
        # msvcrt._putenv_s(name, value)
        msvcrt._putenv('%s=%s' % (name, value))  # Windows XP compatibility


def get_windows_r_user():
    """ Get a reasonable directory for R_USER on Windows.

    We implement the logic described in the R FAQ:

        http://cran.r-project.org/bin/windows/base/rw-FAQ.html#What-are-HOME-and-working-directories_003f
    """
    # 0. R_USER environemnt variable.
    if 'R_USER' in os.environ:
        return os.environ['R_USER']

    # 1. HOME environment variable
    elif 'HOME' in os.environ:
        return os.environ['HOME']

    # 2. "Personal" directory
    import win32api
    import win32con
    try:
        hkey = win32api.RegOpenKeyEx(
            win32con.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders',
            0, win32con.KEY_QUERY_VALUE)
        try:
            personal = win32api.RegQueryValueEx(hkey, 'Personal')[0]
        finally:
            win32api.RegCloseKey(hkey)
    except win32api.error:
        logger.exception('Failed to read Windows personal directory')
    else:
        return os.path.expandvars(personal)

    # 3. HOMEDRIVE/HOMEPATH environment variables.
    if 'HOMEDRIVE' in os.environ and 'HOMEPATH' in os.environ:
        return os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']

    # 4. The current working directory.
    return os.getcwd()


# This calls the R_HOME discovery logic in `rpy2.rinterface.__init__`.
from rpy2 import rinterface

if os.name == 'nt':
    # Amazingly, rpy2 detects and sets the R_HOME environment variable at the
    # Python level, but then can't find it at the C level!
    putenv('R_HOME', os.environ['R_HOME'])

    # The logic in rpy2 for finding R_USER is quite broken:
    #
    #    https://bitbucket.org/lgautier/rpy2/src/387ff4/rpy/rinterface/_rinterface.c?at=default#cl-1204
    #
    # Note that HOME and HOMEDIR are not even valid environment variables in
    # modern versions of Windows. Use our logic instead.
    putenv('R_USER', get_windows_r_user())

# Now we can initialize the R interpreter.
rinterface.initr()
