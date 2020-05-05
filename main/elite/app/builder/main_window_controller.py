from __future__ import absolute_import

import cPickle as pickle
import os
import tempfile

from enaml.layout.api import AreaLayout, HSplitLayout, VSplitLayout
from enaml.widgets.api import FileDialogEx, Window
from pyface.api import OK
from traits.api import Bool, List, Instance, Property, on_trait_change
import traits_enaml

from elite.data.data_source import DataSource
from elite.data.sql_data_source import SQLDataSource
from elite.model import Model, ModelError
from elite.runner import Runner
import enaml
with enaml.imports():
    from enaml.stdlib.message_box import warning
from ..common.app_window_controller import ApplicationWindowController
from ..common.data_source_wizard import DataSourceWizard
from .gui_runner import GUIRunner
from .model_editor_controller import ModelEditorController


class MainWindowController(ApplicationWindowController):
    """ The controller for the Model Builder main window.
    """
    # The currently loaded input data (possibly None).
    input_data = Instance('pandas.DataFrame')
    # The input data source (possibly None).
    input_source = Instance(DataSource)
    # The destination for model results (possibly None).
    output_source = Instance(DataSource)
    temp_output_source = Instance(DataSource)
    # The model being edited.
    model = Instance(Model)
    model_controller = Instance(ModelEditorController)
    file_filters = ['Elite Anomaly Model (*.eam)']
    # Whether the application is in debug mode.
    debug_mode = Bool(False)
    # The layout for the main window.
    dock_area = Property(depends_on='window')
    full_layout = Instance('enaml.layout.dock_layout.LayoutNode')
    layout = Property(Instance('enaml.layout.dock_layout.LayoutNode'), depends_on='dock_area, input_data, full_layout')
    dock_items = Property(List('enaml.widgets.dock_item.DockItem'), depends_on='layout')
    # The state file for the application
    state_filename = 'state_builder.json'

    # --- Application actions ---

    def run_model(self):
        """ Run the model.
        """
        # Validate the model.
        try:
            self.model.validate()
        except ModelError as exc:
            warning(parent=self.window,
                    title='Validation failure',
                    text=str(exc))
            return

        # Make sure we have an input data source.
        if not self.input_source:
            self.select_data_sources()
        if not (self.input_source and self.input_source.can_load):
            return

        # Make sure we have an output data source.
        if self.output_source:
            output_source = self.output_source
        else:
            if not self.temp_output_source:
                f, path = tempfile.mkstemp(prefix='results_', suffix='.sqlite')
                os.close(f)
                self.temp_output_source = SQLDataSource(dialect='sqlite',
                                                        database=path)
            output_source = self.temp_output_source

        # Attempt to run the model.
        runner = Runner(model=self.model,
                        input_source=self.input_source,
                        output_source=output_source)
        gui_runner = GUIRunner(parent=self.window, runner=runner)
        gui_runner.run()

        # If successful, show the results inspector.
        if runner.results:
            # Delay import to improve start-up time.
            from elite.app.inspector.main import create_inspector

            # Close existing inspector window, if necessary.
            for window in Window.windows:
                if window.name == 'inspector':
                    window.close()

            # Create new inspector window.
            inspector_window = create_inspector(results=runner.results)
            inspector_window.show()

    def write_model(self):
        """ Write the model to disk as an R script.
        """
        filters = ['R script (*.R)']
        path = FileDialogEx.get_save_file_name(
            parent=self.window,
            current_path=os.path.splitext(self.file_path)[0] + '.R',
            name_filters=filters,
        )
        if path:
            runner = Runner(model=self.model,
                            input_source=self.input_source,
                            output_source=self.output_source)
            with open(path, 'w') as f:
                runner.write_program(f)

    def select_data_sources(self):
        """ Show a dialog to select the input and output data sources.
        """
        clone = lambda x: x.clone_traits() if x is not None else None
        wizard = DataSourceWizard(parent=self.window.proxy.widget,
                                  input_source=clone(self.input_source),
                                  output_source=clone(self.output_source),
                                  mode='save')
        wizard.open()
        if wizard.return_code == OK:
            self.input_source = wizard.input_source
            self.output_source = wizard.output_source

    def show_debug_console(self):
        """ Show an IPython console for debugging.
        """
        from enaml.layout.api import FloatItem, RemoveItem
        from enaml.widgets.api import Window, Container, DockItem, IPythonConsole

        dock_area = self.dock_area
        name = 'ipython_console'
        item = DockItem(dock_area, name=name, title='Console')
        console_container = Container(item, padding=0)

        console = IPythonConsole(console_container, initial_ns={
            'main_controller': self,
            'windows': Window.windows,
        })
        console.observe('exit_requested', lambda change: \
            dock_area.update_layout(RemoveItem(item=name)))

        dock_area.update_layout(FloatItem(item=name))

    def reset_full_layout(self):
        """ Reset the dock area layout for "full" mode (model + data).
        """
        self.full_layout = self._full_layout_default()

    def confirm_window_close(self, event):
        """ Confirm whether the application can be exited.
        """
        if self.confirm_file_close():
            event.accept()
        else:
            event.ignore()

    # --- Public interface ---

    def add_model_object(self, obj):
        """ An a ModelObject to the model.
        """
        self.model_controller.add_object(obj)

    def remove_model_object(self, obj):
        """ Remove a ModelObject from the model.
        """
        self.model_controller.remove_object(obj)

    # --- ApplicationWindowController interface ---

    def _new_file(self):
        """ Create a new model.
        """
        self.model = Model()
        self.file_dirty = False

    def _load_file(self, f):
        """ Load a model from a file object.
        """
        self.model = Model.load(f)

    def _save_file(self, f):
        """ Save the model to a file object.
        """
        self.model.save(f)

    def destroy(self):
        if self.temp_output_source:
            os.remove(self.temp_output_source.database)
            self.temp_output_source = None

        super(MainWindowController, self).destroy()

    def create_state(self):
        if self.input_data is not None:
            self.full_layout = self.dock_area.save_layout()

        state = super(MainWindowController, self).create_state()
        state['full_layout'] = pickle.dumps(self.full_layout)

        return state

    def restore_state(self, state):
        super(MainWindowController, self).restore_state(state)
        full_layout = state.get('full_layout')
        if full_layout is not None:
            self.full_layout = pickle.loads(str(full_layout))

    # --- Private interface ---

    def _get_layout(self):
        if self.input_data is not None:
            return self.full_layout

        return AreaLayout('model')

    def _get_dock_items(self):
        with traits_enaml.imports():
            from .dock_items import AttributesItem, DataItem, ModelItem

        if self.input_data is not None:
            return [
                AttributesItem(name='attributes'),
                DataItem(name='data'),
                ModelItem(name='model')
            ]

        return [ModelItem(name='model', title_bar_visible=False)]

    # Trait defaults

    def _full_layout_default(self):
        return HSplitLayout(
            'attributes',
            VSplitLayout(
                'model',
                'data',
            ),
            sizes=[150, 650],  # Default widths
        )

    def _model_default(self):
        return Model()

    def _model_controller_default(self):
        return ModelEditorController(model=self.model)

    # Trait property getter/setters

    def _get_dock_area(self):
        if self.window:
            return self.window.find('dock_area')
        return None

    # Trait change handlers

    def _input_source_changed(self, ds):
        data = None
        if ds and ds.can_load:
            # try:
            ds.load_metadata()
            data = ds.load()
            # except Exception as exc:
            #     warning(parent=self.window,
            #             title='Load error',
            #             text='Error loading data',
            #             content=str(exc))

        self.input_data = data

    def _model_changed(self):
        self.model_controller.model = self.model

    @on_trait_change('model.dirtied')
    def _model_dirtied(self):
        self.file_dirty = True
