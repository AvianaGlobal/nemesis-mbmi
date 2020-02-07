from __future__ import absolute_import

from enaml.widgets.api import FileDialogEx
from enaml.widgets.toolkit_dialog import ToolkitDialog


# Monkey patch the _prepare method of the FileDialogEx class so that it
# properly respects the initial selected_name_filter.

def _prepare(self):
    ToolkitDialog._prepare(self)
    self.selected_paths = []

FileDialogEx._prepare = _prepare


def file_type_filters(file_types, default=''):
    """ Generate a list of file type filters of the format "{name} ({exts})"
    from a list of (name, extensions) tuples.

    Returns a 2-tuple of the filter list and the selected filter (or '')
    """
    name_filters = []
    selected_name_filter = ''
    for name, exts in sorted(file_types.iteritems()):
        glob = ' '.join(['*.' + ext for ext in exts])
        name_filter = '{} ({})'.format(name, glob)
        name_filters.append(name_filter)
        if default in exts:
            selected_name_filter = name_filter

    return name_filters, selected_name_filter
