from __future__ import absolute_import
from atom.api import Tuple, set_default
from enaml.core.api import d_, d_func
from enaml.widgets.api import Feature
from traitsui.qt4.clipboard import PyMimeData
from nemesis.ui.field import Field


class DropField(Field):
    """ A field that supports drops and text insertion.
    """
    valid_types = d_(Tuple(default=(basestring,)))
    features = set_default(Feature.DropEnabled)

    # Widget interface.
    def drag_enter(self, event):
        accept = False
        mime_data = event.mime_data()

        # Standard text mimetype
        if mime_data.has_format('text/plain'):
            accept = True
        
        # Support Traits UI table and tabular editors (single selection only).
        elif mime_data.has_format(PyMimeData.MIME_TYPE):
            data = PyMimeData.coerce(mime_data.q_data()).instance()
            accept = (isinstance(data, list) and len(data) == 1 and
                      isinstance(data[0], self.valid_types))
        
        if accept:
            event.accept_proposed_action()
    
    def drop(self, event):
        mime_data = event.mime_data()
        
        if mime_data.has_format('text/plain'):
            text = mime_data.data('text/plain')
        
        elif mime_data.has_format(PyMimeData.MIME_TYPE):
            data = PyMimeData.coerce(mime_data.q_data()).instance()
            text = self.to_string(data[0])
        
        self.insert_text(text)
    
    # DropField interface.

    @d_func
    def to_string(self, data):
        return data
        
    def insert_text(self, text):
        """ Insert text at the current cursor location.
        """
        # XXX: Enaml should have an API for this. We shouldn't have to fish
        # out the toolkit control.
        if self.proxy_is_active:
            line_edit = self.proxy.widget
            line_edit.insert(text)
            self.proxy.on_submit_text()
    
    def set_field_text(self, text):
        """ Set the text in the widget.
        
        Depending on the whether the text validates, this text may be different
        than that stored in the 'text' attribute.
        
        See also 'field_text()'.
        """
        # Expose the proxy method.
        if self.proxy_is_active:
            self.proxy.set_text(text)
            self.proxy.on_submit_text()