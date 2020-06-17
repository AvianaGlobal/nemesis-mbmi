from __future__ import absolute_import

from atom.api import Dict, Unicode
from chaco.api import PlotGraphicsContext
from traits_enaml.widgets.enable_canvas import EnableCanvas

from nemesis.ui.file_dialog import FileDialogEx, file_type_filters
from nemesis.ui.message_box import warning


class ChacoCanvas(EnableCanvas):
    """ An Enaml widget for Chaco plots.
    
    Extends ``EnableCanvas`` with some Chaco-specific features.
    """
    
    # By default, Atom objects are not weak-referencable, but Traits handlers
    # use weak references.
    __slots__ = '__weakref__'

    save_formats = Dict()

    default_save_format = Unicode('png')

    def _default_save_formats(self):
        # Taken from http://doc.qt.io/qt-4.8/qimagewriter.html#supportedImageFormats
        # XPM and XBM are excluded, as they caused errors when trying to save
        # the component plot.
        return {
            'Windows Bitmap file': ['bmp'],
            'Joint Photographic Experts Group file': ['jpg', 'jpeg'],
            'Portable Network Graphics file': ['png'],
            'Portable Pixmap file': ['ppm'],
            'Tagged Image File Format file': ['tiff']
        }

    def save(self):
        """ Show a dialog for saving the figure.
        
        Return whether the figure was successfully saved.
        """
        name_filters, selected_name_filter = file_type_filters(
            self.save_formats, default=self.default_save_format
        )

        filename = FileDialogEx.get_save_file_name(
            parent=self,
            name_filters=name_filters,
            selected_name_filter=selected_name_filter
        )

        if filename:
            gc = PlotGraphicsContext(
                (int(self.component.outer_width),
                 int(self.component.outer_height)))
            self.component.draw(gc, mode="normal")

            try:
                gc.save(filename)

            except Exception as exc:
                warning(parent=self.parent,
                        title='Save Error',
                        text='Error saving figure',
                        content=str(exc))
            else:
                return True

        return False
