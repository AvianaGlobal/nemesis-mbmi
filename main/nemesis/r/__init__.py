import ctypes
import os
import subprocess

import logging
logger = logging.getLogger(__name__)


def putenv(name, value):
    """ Set an environment variable at both the Python and C levels.
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
    import win32api, win32con
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


def get_r_home():
    """ Get a reasonable directory for R_HOME.
    """
    if 'R_HOME' in os.environ:
        return os.environ['R_HOME']

    # Try to get R_HOME from the output of `R RHOME`
    output = subprocess.check_output(['R', 'RHOME'], universal_newlines=True)
    output = output.encode().strip()
    if output:
        return output

    return None


R_HOME = get_r_home()

if R_HOME is None:
    raise EnvironmentError('Unable to find R_HOME')

if os.name == 'nt':
    putenv('R_USER', get_windows_r_user())
else:
    putenv('R_HOME', R_HOME)
