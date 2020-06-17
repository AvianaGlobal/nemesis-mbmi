""" Convenience functions for accessing common application resources.
"""
from __future__ import absolute_import

import functools
import os.path

from enaml.icon import Icon, IconImage
from enaml.image import Image
from enaml.qt.QtGui import QIcon
from pyface.api import ImageResource


def memoize(obj):
    """ The standard memoize decorator.
    """
    cache = obj.cache = {}

    @functools.wraps(obj)
    def memoizer(*args, **kwargs):
        key = args + tuple(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]
    
    return memoizer


@memoize
def get_enaml_image(name, **kwargs):
    path = get_image_path(name)
    with open(path, 'rb') as f:
        data = f.read()
    return Image(data = data, **kwargs)

@memoize
def get_enaml_icon(name, **kwargs):
    image = get_enaml_image(name, **kwargs)
    return Icon(images = [IconImage(image=image)])


@memoize
def get_qt_icon(name):
    path = get_image_path(name)
    return QIcon(path)


def get_image_resource(name):
    path = os.path.dirname(os.path.abspath(__file__))
    return ImageResource(name = name, search_path = [path])
    
def get_image_path(name):
    image_resource = get_image_resource(name)
    return image_resource.absolute_path


def get_toolbar_icon(name):
    """ Get an Enaml icon with the standard size for toolbar icons on this 
    platform.
    """
    import sys
    if sys.platform == 'win32':
        size = (16, 16)
    elif sys.platform == 'darwin':
        size = (16, 16)
    else:
        size = (24, 24) # from GNOME Human Interface Guidelines
    return get_enaml_icon(name, size=size)