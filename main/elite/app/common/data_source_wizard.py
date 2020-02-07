""" A wizard for selecting input and output data sources.
"""
from enaml.qt.qt_application import QtApplication
from enaml.widgets.widget import Widget
from pyface.wizard.api import Wizard, WizardController, WizardPage
from traits.api import DelegatesTo, Enum, Instance, on_trait_change
import traits_enaml
from elite.data.data_source import DataSource
from elite.data.sql_data_source import SQLDataSource

with traits_enaml.imports():
    from .data_source_wizard_views import InputOpenPageView, InputSavePageView, OutputOpenPageView, OutputSavePageView


class DataSourceWizard(Wizard):
    
    # IWindow interface
    
    title = 'Select data sources'
    
    # DataSourceWizard interface

    # Input and output DataSources.
    input_source = DelegatesTo('_input_page', 'data_source')
    output_source = DelegatesTo('_output_page', 'data_source')
    
    # Are we loading existing results ('open') or saving new results ('save')?
    # Note that in 'open' mode, only SQL input data is allowed due to the
    # requirements of RunResults and the results inspector.
    mode = Enum('open', 'save')
    
    # Private interface
    
    _input_page = Instance(WizardPage)
    _output_page = Instance(WizardPage)
    
    # IWizard interface
    
    def _controller_default(self):
        if self.mode == 'open':
            pages = [ self._output_page, self._input_page ]
        else:
            pages = [ self._input_page, self._output_page ]
        return WizardController(pages = pages)
    
    def __input_page_default(self):
        return InputPage(mode = self.mode)
    
    def __output_page_default(self):
        return OutputPage(mode = self.mode)
    
    def _mode_changed(self, mode):
        self._input_page.mode = mode
        self._output_page.mode = mode


class EnamlWizardPage(WizardPage):
    
    # EnamlWidgetPage interface
    
    widget = Instance(Widget)
    
    # IWizardPage interface
    
    def _create_page_content(self, parent):
        widget = self.widget
        if not widget.is_initialized:
            widget.initialize()
        if not widget.proxy_is_active:
            widget.activate_proxy()
        content = widget.proxy.widget
        return content


class InputPage(EnamlWizardPage):
    
    # IWizardPage interface
    
    heading = 'Select an input data source'
    
    # InputPage interface
    
    data_source = Instance(DataSource)
    mode = Enum('open', 'save')
    
    def __init__(self, **traits):
        super(InputPage, self).__init__(**traits)
        self._update_complete()
    
    def _subheading_default(self):
        if self.mode == 'open':
            return 'Load input data from SQL database'
        else:
            return 'Load input data from a flat file or SQL database'
    
    def _widget_default(self):
        if self.mode == 'open':
            widget = InputOpenPageView()
            if self.data_source is not None:
                widget.data_source = self.data_source
        else:
            widget = InputSavePageView(data_source = self.data_source)
        widget.observe('data_source',
            lambda change: self.trait_set(data_source = change['value']))
        return widget
    
    @on_trait_change('data_source.can_load')
    def _update_complete(self):
        if self.mode == 'open' and self.data_source is None:
            self.complete = True
        else:
            self.complete = bool(self.data_source and self.data_source.can_load)


class OutputPage(EnamlWizardPage):
    
    # IWizardPage interface
    
    heading = 'Select a results data source'
    
    # OutputPage interface
    
    data_source = Instance(SQLDataSource)
    mode = Enum('open', 'save')
    
    def __init__(self, **traits):
        super(OutputPage, self).__init__(**traits)
        self._update_complete()
    
    def _subheading_default(self):
        if self.mode == 'open':
            return 'Load results data from SQL database'
        else:
            return 'Save results data to SQL database'
    
    def _widget_default(self):
        if self.mode == 'open':
            widget = OutputOpenPageView()
            if self.data_source is not None:
                widget.data_source = self.data_source
        else:
            widget = OutputSavePageView()
            if self.data_source is not None:
                widget.data_source = self.data_source
        widget.observe('data_source',
            lambda change: self.trait_set(data_source = change['value']))
        return widget
    
    @on_trait_change('data_source.can_connect')
    def _update_complete(self):
        # Complete if no data source (temporary file requested) or valid data 
        # source.
        self.complete = self.data_source is None or self.data_source.can_connect


if __name__ == '__main__':
    import sys
    
    app = QtApplication()
    wizard = DataSourceWizard(mode = 'save')
    wizard.on_trait_change(lambda: sys.exit(), 'closed')
    wizard.open()
    
    app.start()