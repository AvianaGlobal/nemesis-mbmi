from __future__ import absolute_import

from atom.api import Typed, set_default
from pyface.action.api import ActionController
from traits.api import HasStrictTraits, Unicode, Instance, List, Type, Dict, Any
from traitsui.api import Menu, Action

from enaml.core.declarative import d_
from enaml.qt.QtCore import *
from enaml.qt.QtGui import *
from enaml.widgets.raw_widget import RawWidget

from nemesis.model import ModelObject
from nemesis.app.common.resources import get_qt_icon
from nemesis.object_registry import ObjectRegistry
from .model_editor_controller import ModelEditorController

import traits_enaml
with traits_enaml.imports():
    from .model_views import TopLevelModelView, UserCodeView


RemoveAction = Action(
    name='Remove',
    action='controller.remove_object(obj)'
)


class ModelTreeItem(HasStrictTraits):
    """ An item within a ModelTree. Used to compose the data for the model
    tree view.
    """
    title = Unicode()
    icon = Instance(QIcon)
    model_object = Instance(ModelObject)
    parent = Instance('ModelTreeItem')
    controller = Instance(ModelEditorController)

    ui = Type(klass='enaml.widgets.widget.Widget', value=None)
    ui_kwargs = Dict(Unicode, Any)
    menu = Instance(Menu)

    _children = List(Instance('ModelTreeItem'))

    @classmethod
    def from_model_object(cls, model_object, **kwargs):
        return cls(title=model_object.name, model_object=model_object, **kwargs)

    def append_child(self, child):
        child.parent = self
        self._children.append(child)

    def child(self, row):
        if 0 <= row < len(self._children):
            return self._children[row]
        return None

    def child_count(self):
        return len(self._children)

    def row(self):
        if self.parent:
            return self.parent._children.index(self)
        return 0

    def select(self):
        self.controller.selected_object = self.model_object
        self.controller.selected_ui = self.ui_instance()

    def default_ui(self):
        klass = type(self.model_object)
        factory = ObjectRegistry.instance().get_closest_by_type(klass)
        return factory.ui if factory else None

    def ui_instance(self):
        ui_klass = self.ui if self.ui else self.default_ui()
        if not ui_klass:
            return None

        return ui_klass(**dict(self.ui_kwargs))


class ModelTreeModel(QAbstractItemModel):
    """ The Qt item model for a tree view, populated by a model controller.
    """
    def __init__(self, controller, parent=None):
        super(ModelTreeModel, self).__init__(parent)
        self.controller = controller
        self.populate(controller.model)

    def populate(self, model):
        root = ModelTreeItem()

        model_item = ModelTreeItem(
            title='Model', icon=get_qt_icon('model.png'),
            controller=self.controller, ui=TopLevelModelView,
            ui_kwargs={'model': model}

        )
        root.append_child(model_item)

        icon_provider = QFileIconProvider()
        folder_icon = icon_provider.icon(QFileIconProvider.Folder)

        controls_item = ModelTreeItem(
            title='Controls', icon=folder_icon, controller=self.controller
        )
        model_item.append_child(controls_item)

        for control in model.controls:
            item = ModelTreeItem.from_model_object(
                control, icon=get_qt_icon('control.png'),
                controller=self.controller, ui_kwargs={'obj': control},
                menu=Menu(RemoveAction)
            )
            controls_item.append_child(item)

        metrics_item = ModelTreeItem(
            title='Metrics', icon=folder_icon, controller=self.controller
        )
        model_item.append_child(metrics_item)

        for metric in model.metrics:
            item = ModelTreeItem.from_model_object(
                metric, icon=get_qt_icon('metric.png'),
                controller=self.controller, ui_kwargs={'obj': metric},
                menu=Menu(RemoveAction)
            )
            metrics_item.append_child(item)

        composite_item = ModelTreeItem(
            title='Composite Scores', icon=folder_icon,
            controller=self.controller
        )
        model_item.append_child(composite_item)

        for composite in model.composite_scores:
            item = ModelTreeItem.from_model_object(
                composite, icon=get_qt_icon('composite_score.png'),
                controller=self.controller, ui_kwargs={'obj': composite},
                menu=Menu(RemoveAction)
            )
            composite_item.append_child(item)

        custom_item = ModelTreeItem(
            title='Custom Code', icon=get_qt_icon('code.png'),
            controller=self.controller, ui=UserCodeView,
            ui_kwargs={'model': model}

        )
        model_item.append_child(custom_item)

        self._root_item = root

    def index_of(self, obj):
        return self._index_of_helper(obj, self._root_item)

    def _index_of_helper(self, obj, node):
        if node.model_object == obj:
            return self.createIndex(node.row(), 0, node)

        index = QModelIndex()
        for child in node._children:
            child_index = self._index_of_helper(obj, child)
            if child_index.isValid():
                index = child_index
                break

        return index

    def index(self, row, column, parent_index=None, *args, **kwargs):
        if not parent_index or not self.hasIndex(row, column, parent_index):
            return QModelIndex()

        if parent_index.isValid():
            parent_item = parent_index.internalPointer()
        else:
            parent_item = self._root_item

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)

        return QModelIndex()

    def parent(self, index=None):
        if not index or not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if not parent_item or parent_item == self._root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent_index=None, *args, **kwargs):
        if not parent_index or parent_index.column() > 0:
            return 0

        if parent_index.isValid():
            parent_item = parent_index.internalPointer()
        else:
            parent_item = self._root_item

        return parent_item.child_count()

    def columnCount(self, parent_index=None, *args, **kwargs):
        return 1

    def data(self, index, role=None):
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.title

        elif role == Qt.DecorationRole:
            return item.icon

        elif role == Qt.UserRole:
            return item

        return None

    def flags(self, index):
        if not index.isValid():
            return 0

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class ModelTree(RawWidget):
    """ A widget that displays a tree widget for a model controller.
    """
    __slots__ = '__weakref__'

    controller = d_(Typed(ModelEditorController))

    hug_width = set_default('weak')
    hug_height = set_default('weak')

    def create_widget(self, parent):
        widget = QTreeView(parent)
        widget.setHeaderHidden(True)
        widget.setSelectionMode(QAbstractItemView.SingleSelection)
        widget.setContextMenuPolicy(Qt.CustomContextMenu)
        widget.customContextMenuRequested.connect(self._on_menu)
        self.set_controller(self.controller, widget=widget)

        return widget

    def set_controller(self, controller, widget=None):
        if not widget:
            widget = self.get_widget()

        if widget and controller:
            widget.setModel(ModelTreeModel(controller))
            widget.selectionModel().currentChanged.connect(
                self._selection_changed
            )
            self.hook_controller(controller)
            widget.expandAll()

    def hook_controller(self, controller, unhook=False):
        if not controller:
            return

        controller.on_trait_change(self._update_controller, 'model', unhook)
        controller.on_trait_change(self._update_selected, 'selected_object', unhook)

        model = controller.model
        if model:
            model.on_trait_change(self._update_controller, 'controls.name', unhook)
            model.on_trait_change(self._update_controller, 'metrics.name', unhook)
            model.on_trait_change(self._update_controller, 'composite_scores.name', unhook)

    def _observe_controller(self, change):
        if change['type'] == 'update':
            old_controller = change.get('old_value')
            self.hook_controller(old_controller, unhook=True)

            controller = change['value']
            self.set_controller(controller)

    def _update_controller(self):
        self.set_controller(self.controller)

    def _selection_changed(self, index, old_index):
        widget = self.get_widget()
        if widget:
            item = widget.model().data(index, role=Qt.UserRole)
            item.select()

    def _update_selected(self, obj):
        widget = self.get_widget()
        if widget:
            index = widget.model().index_of(obj)
            if index.isValid():
                item = widget.model().data(index, role=Qt.UserRole)
                self.controller.selected_ui = item.ui_instance()
                widget.selectionModel().select(index,
                                               QItemSelectionModel.Select)

    def _on_menu(self, point):
        widget = self.get_widget()
        if widget:
            index = widget.indexAt(point)
            item = widget.model().data(index, role=Qt.UserRole)
            if item and item.menu:
                controller = TreeMenuController(controller=self.controller,
                                                item=item)
                q_menu = item.menu.create_menu(widget, controller=controller)
                q_menu.exec_(widget.mapToGlobal(point))


class TreeMenuController(ActionController):
    controller = Instance(ModelEditorController)
    item = Instance(ModelTreeItem)

    def perform(self, action, event):
        eval(action.action, globals(), {
            'controller': self.controller,
            'obj': self.item.model_object
        })
