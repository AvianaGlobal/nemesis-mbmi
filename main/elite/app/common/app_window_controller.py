from __future__ import absolute_import

import json
import logging
import os

from traits.api import HasTraits, Bool, File, Instance, List, Property, \
    Unicode, on_trait_change
from enaml.widgets.api import FileDialogEx
from elite.ui.message_box import details_escape, warning, DialogButton
from .etsconfig import ETSConfig

logger = logging.getLogger('elite')


class ApplicationWindowController(HasTraits):
    """ The base class for top-level (application-level) window controllers.
    At present, this class mainly provides a light-weight interface for saving
    and restoring application state, such as window size and position.
    """
    # The main window being managed.
    window = Instance('enaml.widgets.api.MainWindow')
    # The name of the currently opened file
    file_name = Property(Unicode, depends_on='file_path')
    # The path to the currently opened file
    file_path = File()
    # A list of file filters for valid files
    file_filters = List(Unicode)
    # The title for the application window, based on the currently open file
    file_title = Property(Unicode, depends_on='file_dirty, file_name')
    # Whether the currently opened file has been edited
    file_dirty = Bool(False)
    # Files that have been opened recently, in descending chronological order.
    recent_files = List(File)
    # Name of the state file for the application
    state_file = Unicode('state.json')
    # Private attributes.
    _state_path = File()

    # --- ApplicationWindowController interface ---
    def __init__(self, **traits):
        super(ApplicationWindowController, self).__init__(**traits)
        state = self._load_state()
        if state is not None:
            try:
                self.restore_state(state)
            except:
                logger.exception('Error restoring application state')

    def destroy(self):
        """ Called immediately before the window is destroyed.
        Can be used to save state and clean up resources.
        """
        try:
            state = self.create_state()
        except:
            logger.exception('Error creating application state object')
        else:
            self._save_state(state)

    def create_state(self):
        """ Create a dictionary capturing the current application state.
        Must be JSON-serializable.
        """
        state = {}
        state['position'] = self.window.position()
        state['size'] = self.window.size()
        state['recent_files'] = self.recent_files
        return state

    def restore_state(self, state):
        """ Restore the application state from a state dictionary.
        """
        position = state.get('position')
        size = state.get('size')
        window = self.window

        if window is not None:
            if position is not None:
                window.initial_position = tuple(position)
                # window.set_position(position)
            if size is not None:
                window.initial_size = tuple(size)
                # window.set_size(size)

        self.recent_files = state.get('recent_files', [])

    # File interface

    def _new_file(self):
        """ Handle a new file creation. This method should be implemented on
        subclasses.
        """
        pass

    def new_file(self):
        """ Create a new file.
        """
        if self.confirm_file_close():
            self._new_file()
            self.file_path = ''

    def open_file(self):
        """ Show a dialog to load an existing file from disk.
        """
        path = FileDialogEx.get_open_file_name(
            parent=self.window, name_filters=self.file_filters)
        if path and self.confirm_file_close():
            self.load_file(path)

    def save_file(self):
        """ Save the file to disk.

        Returns whether the file was saved.
        """
        if self.file_path:
            self.save_file_to(self.file_path)
            return True
        else:
            return self.save_file_as()

    def save_file_as(self):
        """ Show a dialog to save the file to disk.

        Returns whether the file was saved.
        """
        path = FileDialogEx.get_save_file_name(
            parent=self.window, name_filters=self.file_filters)
        if path:
            self.save_file_to(path)
            return True
        return False

    def _load_file(self, f):
        """ Handle a file load. This method should be implemented on subclasses.
        """
        pass

    def load_file(self, path):
        """ Load a file from the specified path.
        """
        try:
            with file(path, 'r') as f:
                self._load_file(f)
        except Exception as exc:
            warning(parent=self.window,
                    title='Load error',
                    text='Load error',
                    content='An error occurred while loading the file.',
                    details=details_escape(str(exc)))
        else:
            self.file_path = path
            self.file_dirty = False
            self.add_recent_file(path)

    def _save_file(self, f):
        """ Handle a file save. This method should be implemented on subclasses.
        """
        pass

    def save_file_to(self, path):
        """ Save the file to the specified path.
        """
        try:
            with file(path, 'w') as f:
                self._save_file(f)
        except Exception as exc:
            warning(parent=self.window,
                    title='Save error',
                    text='Save error',
                    content='An error occurred while saving the file.',
                    details=details_escape(str(exc)))
        else:
            self.file_path = path
            self.file_dirty = False
            self.add_recent_file(path)

    def add_recent_file(self, path):
        """ Add a model file to the list of recent models.
        """
        path = os.path.abspath(path)
        recent = self.recent_files[:]
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self.recent_files = []  # XXX: force update
        self.recent_files = recent[0:10]

    def confirm_file_close(self):
        """ Confirm whether the current file can be closed.
        """
        if self.file_dirty:
            button = warning(
                parent=self.window,
                title='Close file?',
                text='The current file has unsaved changes.',
                content='Do you want to save these changes?',
                buttons=[DialogButton('Yes', 'accept'),
                         DialogButton('No', 'accept'),
                         DialogButton('Cancel', 'reject')],
            )
            return button and ((button.text == 'Yes' and self.save_file()) or
                               button.text == 'No')
        else:
            return True

    # --- Application actions ---

    def window_closed(self, event):
        """ Called when the window is closed, immediately before destruction.
        """
        self.destroy()

    # --- Private interface ---

    def _load_state(self):
        """ Load application state dictionary from previous run.
        """
        if not os.path.exists(self._state_path):
            return None
        try:
            with open(self._state_path, 'r') as f:
                state = json.load(f)
            assert isinstance(state, dict)
        except (AssertionError, IOError):
            logger.exception('Error loading application state from disk')
            return None
        else:
            return state

    def _save_state(self, state):
        """ Save application state dictionary for next run.
        """
        try:
            with open(self._state_path, 'w') as f:
                json.dump(state, f)
        except IOError:
            logger.exception('Error saving application state to disk')

    # Trait defaults

    def __state_path_default(self):
        home = ETSConfig.application_data
        if not os.path.exists(home):
            os.mkdir(home)
        return os.path.join(home, self.state_filename)

    # Trait getters/setters

    def _get_file_name(self):
        if self.file_path:
            name = os.path.splitext(os.path.basename(self.file_path))[0]
        else:
            name = 'untitled'
        return name

    def _get_file_title(self):
        title = self.file_name
        if self.file_dirty:
            title += '*'
        return title

    # Trait change handlers

    @on_trait_change('window')
    def _replace_controller(self):
        if self.window:
            self.window.main_controller = self