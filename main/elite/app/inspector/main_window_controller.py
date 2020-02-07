from __future__ import absolute_import

import logging
import cPickle as pickle
import json
import os

import pandas as pd
import sqlalchemy

from enaml.layout.api import InsertTab, ItemLayout, HSplitLayout, VSplitLayout
from pyface.api import OK
from traits.api import Bool, Instance, List, Property, Str, Unicode,\
    on_trait_change, cached_property
import traits_enaml

from elite.app.common.preferences import Preferences, INSPECTOR
from elite.data.variable import Variable
from elite.data.ui.sql_table_model import SQLTableModel
from elite.run_results import RunResults
from elite.ui.message_box import warning, question
from ..common.app_window_controller import ApplicationWindowController
from ..common.data_source_wizard import DataSourceWizard
from ..common.resources import get_enaml_icon

with traits_enaml.imports():
    from .dock_items import BarPlotItem, BoxPlotItem, HistogramItem, \
        ScatterPlotItem


logger = logging.getLogger('elite')


PLOT_TYPES = {
    'bar': BarPlotItem,
    'box': BoxPlotItem,
    'histogram': HistogramItem,
    'scatter': ScatterPlotItem,
}


class MainWindowController(ApplicationWindowController):
    """ The controller for the Results Inspector main window.
    """
    
    # --- Required attributes ---
    
    # The run results being inspected.
    results = Instance('elite.run_results.RunResults')
    
    # --- Optional attributes ---
    
    # Label to use for population data in plots.
    # Should not coincide with any group ID.
    label_pop = Str('Population')

    # The valid types of files for this application
    file_filters = ['Elite Anomaly Session (*.eas)']
    
    # --- Window state ---

    # The state file for the application
    state_filename = 'state_inspector.json'
    
    # The displayed table of input data.
    input_data = Instance(pd.DataFrame)
    
    # The name of the table of group metric/score data.
    result_table = Str('group_results')

    # The table model that accesses the result table.
    results_model = Property(Instance(SQLTableModel),
                             depends_on=['result_table', 'results'])

    # The metric and metric scores.
    result_variables = List(Variable)

    # Whether the groups are of size 1 and represent entities.
    groups_are_entities = Property(Bool, depends_on='results')

    # The input data column used to link size 1 groups to a set of entities.
    link_column = Str
    
    # The selected groups in the metric data table.
    selected_groups = List()
    
    # Status bar text describing the current selection.
    selection_status_text = Unicode()
    
    # Suffix to append to score columns to distinguish them from value columns.
    metric_score_suffix = Str('_Score')
    
    # The metric score variables in the combined result data table.
    metric_score_vars = List(Variable)
    
    # Are the status icons enabled for the score columns?
    dashboard_mode = Bool(False)
    
    # The dock area attached to the main window.
    dock_area = Property(depends_on='window')
    base_layout = Instance('enaml.layout.dock_layout.LayoutNode')
    
    # --- Application actions ---

    def entity_plot_drag(self, widget, drag_data):
        """ Validate drag enter for entity-level plot.
        """
        return isinstance(drag_data, list)
    
    def entity_plot_drop(self, widget, drag_data):
        """ Handle drop onto entity-level plot.
        """
        if all(isinstance(obj, Variable) for obj in drag_data):
            return self.update_entity_plot_variables(widget, drag_data)
        return self.update_entity_plot_groups(widget, drag_data)

    def reset_dock_area(self):
        """ Close any dock panes created by the user.
        """
        base_layout = self._base_layout_default()
        base_names = { node.name for node in base_layout.find_all(ItemLayout) }
        for item in self.dock_area.dock_items():
            if item.name not in base_names:
                item.destroy()
    
    def reset_layout(self):
        """ Reset the dock area layout to the default.
        
        Closes any dock panes created by the user.
        """
        self.reset_dock_area()
        self.base_layout = self._base_layout_default()
        self.dock_area.layout = self.base_layout
    
    def show_plot(self, plot_type, **traits):
        """ Show a plot in a new tab.
        """
        item = PLOT_TYPES[plot_type](**traits)
        op = InsertTab(target = 'input_table')
        self.add_dock_item(item, op)

    def confirm_window_close(self, event):
        """ Confirm whether the application can be exited.
        """
        if self.confirm_file_close():
            event.accept()
        else:
            event.ignore()
    
    # --- Public interface ---
    
    def __init__(self, **traits):
        super(MainWindowController, self).__init__(**traits)
        self.dock_area.layout = self.base_layout

        self._create_variables()
        self._update_input_data()

    def add_dock_item(self, item, op):
        """ Add a dock item to the dock area.
        
        If no name is defined, a name is generated automatically.
        """
        if not item.name:
            item.name = str(id(item))
        op.item = item.name
        
        self._update_base_layout()
        dock_area = self.dock_area
        item.set_parent(dock_area)
        dock_area.update_layout(op)
    
    def load_entity_plot_data(self, table, columns=None, pop=True, groups=None):
        """ Load data for an entity-level plot.
        
        The data is returned in "long" format with respect to the groups.
        """
        dfs = []
        results = self.results
        group_name = results.group_name
        if columns is not None and group_name not in columns:
            columns = [group_name] + columns
        
        # Load the population data.
        load_args = dict(
            index_col = None,                   # Discard entity ID
            columns = columns,
            coerce_types = { group_name: str }, # Coerce group ID to string
        )
        if pop:
            pref = Preferences.instance(INSPECTOR)
            sample_pop = pref.get('sample_pop')
            if sample_pop:
                sample_pop_size = pref.get('sample_pop_size')
                df = results.sample_data(table, sample_pop_size, **load_args)
            else:
                df = results.load_data(table, **load_args)
            df[group_name] = self.label_pop
            dfs.append(df)
        
        # Load the group data.
        if groups is not None and len(groups) > 0:
            where = sqlalchemy.sql.column(group_name).in_(map(str, groups))
            df = results.load_data(table, where=where, order_by=group_name,
                                   **load_args)
            dfs.append(df)
        
        if dfs:
            return pd.concat(dfs, axis=0, ignore_index=True, copy=False)
        return None
    
    def result_data_decoration(self, row, col, value):
        """ Get the cell decoration for the result table.
        """
        score_names = [v.name for v in self.metric_score_vars]
        score_names.extend([v.name for v in self.results.composite_score_vars])

        if self.dashboard_mode and col in score_names:
            if value >= 3:
                return get_enaml_icon('status_red')
            elif value >= 2:
                return get_enaml_icon('status_yellow')
            else:
                return get_enaml_icon('status_green')
        return None
    
    def update_entity_plot_variables(self, widget, variables):
        """ Set new variables for an entity-level plot.
        """
        # Determine the table to load from.
        sources = { var.source for var in variables }
        if len(sources) != 1:
            raise ValueError('Variables must come from exactly one source')
        source = sources.pop()

        if source == 'input':
            table = 'input'
        elif source in ('metric_value', 'metric_score', 'composite_score'):
            table = 'group_results'
        else:
            content = "There is no entity-level data with name '{name}'"\
                .format(name = variables[0].name)
            warning(parent = self.window,
                    title = 'No data',
                    text = 'Data not available',
                    content = content)
            return False
        
        # Load the data.
        columns = [ var.name for var in variables ]
        if widget.data_frame is not None:
            # Use existing groups, if possible.
            group_name = self.results.group_name
            groups = widget.data_frame[group_name].unique()
        else:
            groups = None

        try:
            df = self.load_entity_plot_data(
                table, columns=columns, pop=True, groups=groups
            )
        except KeyError:
            content = 'This metric does not apply at the individual record '\
                    'level and can only be used for group level plots.'
            warning(parent=self.window, title='Invalid data',
                    text='Invalid data for plot', content=content)
            return False
        
        # Update the plot widget.
        if widget.validate_drop(df, columns):
            with widget.suppress_notifications():
                widget.data_frame = df
                widget.data_columns = columns
                widget.data_info = dict(table = table)
            widget.reset_figure()
            return True
        return False
    
    def update_entity_plot_groups(self, widget, groups):
        """ Set new groups for an entity-level plot.
        """
        results = self.results
        group_name = results.group_name

        # Keep only population data
        df = widget.data_frame
        df = df[df[group_name] == self.label_pop]
        
        if len(groups) > 0:
            group_df = self.load_entity_plot_data(
                table = widget.data_info['table'],
                columns = df.columns,
                pop = False, groups = groups)
            df = pd.concat([df, group_df], ignore_index=True, copy=False)
        
        widget.data_frame = df
        return True

    # --- Session interface ---

    def create_session(self):
        window = self.window
        return {
            'results': pickle.dumps(self.results),
            'dashboard_mode': self.dashboard_mode,
            'result_explorer': window.find('result_explorer').save_state(),
            'input_explorer': window.find('input_explorer').save_state()
        }

    def restore_session(self, state):
        results = state.get('results')
        if results is not None:
            self.results = pickle.loads(str(results))

        dashboard_mode = state.get('dashboard_mode')
        if dashboard_mode is not None:
            self.dashboard_mode = dashboard_mode

        result_state = state.get('result_explorer')
        if result_state is not None:
            res_exp = self.window.find('result_explorer')
            res_exp.restore_state(result_state)
            # XXX: This line is used because the selected_groups trait
            # change handlers do not fire.
            self.selected_groups = res_exp.selected

        input_state = state.get('input_explorer')
        if input_state is not None:
            self.window.find('input_explorer').restore_state(input_state)
    
    # --- ApplicationWindowController interface ---
    
    def create_state(self):
        self._update_base_layout()
        state = super(MainWindowController, self).create_state()
        state['base_layout'] = pickle.dumps(self.base_layout)
        return state
    
    def restore_state(self, state):
        super(MainWindowController, self).restore_state(state)
        base_layout = state.get('base_layout')
        if base_layout is not None:
            self.base_layout = pickle.loads(str(base_layout))

    def _new_file(self):
        """ Open results data for inspection.
        """
        clone = lambda x: x.clone_traits() if x is not None else None
        wizard = DataSourceWizard(
            input_source=clone(self.results.input_source),
            output_source=clone(self.results.output_source),
            mode='open')
        wizard.open()
        if wizard.return_code == OK:
            try:
                self.results = RunResults(input_source=wizard.input_source,
                                          output_source=wizard.output_source)
                self.session_file = ''
            except Exception as exc:
                warning(parent=self.window,
                        title='Load error',
                        text='Error loading results',
                        content=str(exc))

    def _save_file(self, f):
        json.dump(self.create_session(), f)

    def _load_file(self, f):
        self.restore_session(json.load(f))

    # --- Private interface ---
    
    def _create_variables(self):
        """ Process the variables from the run results.
        """ 
        # Merge metric values and scores.
        results = self.results
        if results is None:
            return
        
        # Create corresponding Variables.
        metric_vars = results.metric_vars
        score_vars = results.metric_score_vars
        variables = (results.attribute_vars +
                     results.composite_score_vars +
                     sorted(metric_vars + score_vars, key = lambda v: v.name))
        
        self.metric_score_vars = score_vars
        self.result_variables = variables
    
    def _update_base_layout(self):
        """ Update `base_layout` with the current dock area layout.
        """
        def item_names(layout):
            return { node.name for node in layout.find_all(ItemLayout) }
            
        default_layout = self._base_layout_default()
        layout = self.dock_area.save_layout()
        if item_names(default_layout) == item_names(layout):
            self.base_layout = layout
    
    # Trait defaults
    
    def _base_layout_default(self):
        return HSplitLayout(
            VSplitLayout(
                'result_variables',
                'input_variables',
                sizes = [300, 300],
            ),
            VSplitLayout(
                'result_table',
                'input_table',
                sizes = [300, 300],
            ),
            sizes = [200, 1024 - 200], # Default widths
        )

    def _link_column_default(self):
        return self.results.group_name
        
    # Trait property getter/setters
    
    def _get_dock_area(self):
        if self.window:
            return self.window.find('dock_area')
        return None

    @cached_property
    def _get_results_model(self):
        results = self.results

        if not results or not results.output_source:
            return None

        columns = [results.group_name] + [v.name for v in self.result_variables]
        return SQLTableModel(results.output_source.create_engine(),
                             self.result_table,
                             results.group_name,
                             columns)

    def _get_groups_are_entities(self):
        if not self.results.entity_name or not self.results.group_name:
            return False
        return self.results.entity_name == self.results.group_name
    
    # Trait change handlers
    
    def _results_changed(self):
        if not self.traits_inited():
            return
        self.reset_dock_area()
        self._create_variables()

        if self.results and not self.link_column:
            self.link_column = self.results.group_name

        self._update_input_data()

    @on_trait_change('selected_groups, link_column')
    def _update_input_data(self):
        """ Retrieve input data according to which groups are selected.
        """
        results = self.results
        if results is None:
            return

        if len(self.selected_groups) != 0:
            group_where = sqlalchemy.sql.column(results.group_name)\
                .in_(map(str, self.selected_groups))
            engine = self.results.output_source.create_engine()

            if self.groups_are_entities:
                entity_df = results.load_data('input', index_col=None,
                                              where=group_where)
                value = unicode(entity_df[self.link_column][0])
                where = sqlalchemy.sql.column(self.link_column) == value
                query = sqlalchemy.select([sqlalchemy.func.count()]).\
                    select_from(sqlalchemy.table('input')).where(where)

            else:
                where = group_where
                query = sqlalchemy.select([
                    sqlalchemy.func.sum(sqlalchemy.column('Size'))
                ]).select_from(sqlalchemy.table(self.result_table)).where(where)

            records = engine.execute(query).fetchone()[0]
            pref = Preferences.instance(INSPECTOR)
            threshold = pref.get('sample_data_threshold')

            if records > threshold and self._check_sample_threshold(threshold):
                df = results.sample_data('input', threshold, where=where)
            else:
                df = results.load_data('input', where=where)

            text = u'Selected {groups} groups with ' \
                    '{entities} total entities'.format(
                        groups = len(self.selected_groups),
                        entities = records)
        else:
            df = results.load_data('input', limit = 0)
            text = u'No groups selected'

        self.input_data = df
        self.selection_status_text = text

    def _check_sample_threshold(self, threshold):
        button = question(parent=self.window,
                          title='Large number of records',
                          text='A large number of records were found.',
                          content='Loading all of these records could be '
                                  'slow. Do you want to randomly sample the '
                                  'first {}? Selecting No will load all of '
                                  'the records.'.format(threshold))
        return button and button.action == 'accept'

    def _dashboard_mode_changed(self, on):
        """ Force a refresh when dashboard mode is changed.
        """
        model = self.window.find('result_explorer').model
        model.set_columns(model.get_columns())

    @on_trait_change('selected_groups', 'dashboard_mode')
    def _dirtied(self):
        self.file_dirty = True