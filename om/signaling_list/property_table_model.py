# The MIT License (MIT)
#
# Copyright (c) 2015 WUSTL ZPLAB
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Authors: Erik Hvatum <ice.rikh@gmail.com>

import ctypes
from PyQt5 import Qt

class PropertyTableModel(Qt.QAbstractTableModel):
    """PropertyTableModel: Glue for making a Qt.TableView (or similar) in which the elements of a
    SignalingList are rows whose columns contain the values of the element properties specified in
    the property_names argument supplied to PropertyTableModel's constructor.

    On a per-element basis, PropertyTableModel attempts to connect to element."property_name"_changed
    signals.  If an element provides a _changed signal for a column's property, PropertyTableModel
    will connect to it and cause all associated views to update the appropriate cells when the that
    _changed signal is emitted.

    Duplicate elements are fully supported.

    Additionally, "properties" may be plain attributes, with the limitation that changes to plain
    attributes will not be detected.

    An example of a widget containing an editable, drag-and-drop reorderable table containing
    the x, y, and z property values of a SignalingList's elements:

    from PyQt5 import Qt
    from ris_widget import om

    class PosTableWidget(Qt.QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.model = PosTableModel(('x', 'y', 'z'), om.SignalingList(), self)
            self.view = PosTableView(self.model, self)
            self.setLayout(Qt.QVBoxLayout())
            self.layout().addWidget(self.view)

        @property
        def positions(self):
            return self.model.signaling_list

        @positions.setter
        def positions(self, v):
            self.model.signaling_list = v

    class PosTableView(Qt.QTableView):
        def __init__(self, model, parent=None):
            super().__init__(parent)
            self.horizontalHeader().setSectionResizeMode(Qt.QHeaderView.ResizeToContents)
            self.setDragDropOverwriteMode(False)
            self.setDragEnabled(True)
            self.setAcceptDrops(True)
            self.setDragDropMode(Qt.QAbstractItemView.InternalMove)
            self.setDropIndicatorShown(True)
            self.setSelectionBehavior(Qt.QAbstractItemView.SelectRows)
            self.setSelectionMode(Qt.QAbstractItemView.SingleSelection)
            self.delete_current_row_action = Qt.QAction(self)
            self.delete_current_row_action.setText('Delete current row')
            self.delete_current_row_action.triggered.connect(self._on_delete_current_row_action_triggered)
            self.delete_current_row_action.setShortcut(Qt.Qt.Key_Delete)
            self.delete_current_row_action.setShortcutContext(Qt.Qt.WidgetShortcut)
            self.addAction(self.delete_current_row_action)
            self.setModel(model)

        def _on_delete_current_row_action_triggered(self):
            sm = self.selectionModel()
            m = self.model()
            if None in (m, sm):
                return
            midx = sm.currentIndex()
            if midx.isValid():
                m.removeRow(midx.row())

    class PosTableModel(om.signaling_list.DragDropModelBehavior, om.signaling_list.PropertyTableModel):
        pass

    class Pos(Qt.QObject):
        changed = Qt.pyqtSignal(object)

        def __init__(self, x=None, y=None, z=None, parent=None):
            super().__init__(parent)
            for property in self.properties:
                property.instantiate(self)
            self.x, self.y, self.z = x, y, z

        properties = []

        def component_default_value_callback(self):
            pass

        def take_component_arg_callback(self, v):
            if v is not None:
                return float(v)

        x = om.Property(
            properties,
            "x",
            default_value_callback=component_default_value_callback,
            take_arg_callback=take_component_arg_callback)

        y = om.Property(
            properties,
            "y",
            default_value_callback=component_default_value_callback,
            take_arg_callback=take_component_arg_callback)

        z = om.Property(
            properties,
            "z",
            default_value_callback=component_default_value_callback,
            take_arg_callback=take_component_arg_callback)

        for property in properties:
            exec(property.changed_signal_name + ' = Qt.pyqtSignal(object)')
        del property"""

    def __init__(self, property_names, signaling_list=None, parent=None):
        super().__init__(parent)
        self._signaling_list = None
        self.property_names = list(property_names)
        self.property_columns = {pn : idx for idx, pn in enumerate(self.property_names)}
        assert all(map(lambda p: isinstance(p, str) and len(p) > 0, self.property_names)), 'property_names must be a non-empty iterable of non-empty strings.'
        if len(self.property_names) != len(set(self.property_names)):
            raise ValueError('The property_names argument contains at least one duplicate.')
        self._property_changed_slots = [lambda element, pn=pn: self._on_property_changed(element, pn) for pn in self.property_names]
        self._instance_counts = {}
        self.signaling_list = signaling_list

    def rowCount(self, _=None):
        sl = self.signaling_list
        return 0 if sl is None else len(sl)

    def columnCount(self, _=None):
        return len(self.property_names)

    def flags(self, midx):
        f = Qt.Qt.ItemIsSelectable | Qt.Qt.ItemNeverHasChildren
        if midx.isValid():
            f |= Qt.Qt.ItemIsEnabled | Qt.Qt.ItemIsEditable
        f |= self.drag_drop_flags(midx)
        return f

    def drag_drop_flags(self, midx):
        return 0

    def data(self, midx, role=Qt.Qt.DisplayRole):
        if midx.isValid() and role in (Qt.Qt.DisplayRole, Qt.Qt.EditRole):
            return Qt.QVariant(getattr(self.signaling_list[midx.row()], self.property_names[midx.column()]))
        return Qt.QVariant()

    def setData(self, midx, value, role=Qt.Qt.EditRole):
        if midx.isValid() and role == Qt.Qt.EditRole:
            setattr(self.signaling_list[midx.row()], self.property_names[midx.column()], value)
            return True
        return False

    def headerData(self, section, orientation, role=Qt.Qt.DisplayRole):
        if orientation == Qt.Qt.Vertical:
            if role == Qt.Qt.DisplayRole and 0 <= section < self.rowCount():
                return Qt.QVariant(section)
        elif orientation == Qt.Qt.Horizontal:
            if role == Qt.Qt.DisplayRole and 0 <= section < self.columnCount():
                return Qt.QVariant(self.property_names[section])
        return Qt.QVariant()

    def removeRows(self, row, count, parent=Qt.QModelIndex()):
#       print('removeRows', row, count, parent)
        try:
            del self.signaling_list[row:row+count]
            return True
        except IndexError:
            return False

    @property
    def signaling_list(self):
        return self._signaling_list

    @signaling_list.setter
    def signaling_list(self, v):
        if v is not self._signaling_list:
            if self._signaling_list is not None or v is not None:
                self.beginResetModel()
                try:
                    if self._signaling_list is not None:
                        self._signaling_list.inserting.disconnect(self._on_inserting)
                        self._signaling_list.inserted.disconnect(self._on_inserted)
                        self._signaling_list.replaced.disconnect(self._on_replaced)
                        self._signaling_list.removing.disconnect(self._on_removing)
                        self._signaling_list.removed.disconnect(self._on_removed)
                        self._detach_elements(self._signaling_list)
                    assert len(self._instance_counts) == 0
                    self._signaling_list = v
                    if v is not None:
                        v.inserting.connect(self._on_inserting)
                        v.inserted.connect(self._on_inserted)
                        v.replaced.connect(self._on_replaced)
                        v.removing.connect(self._on_removing)
                        v.removed.connect(self._on_removed)
                        self._attach_elements(v)
                finally:
                    self.endResetModel()

    def _attach_elements(self, elements):
        for element in elements:
            instance_count = self._instance_counts.get(element, 0) + 1
            assert instance_count > 0
            self._instance_counts[element] = instance_count
            if instance_count == 1:
                for property_name, changed_slot in zip(self.property_names, self._property_changed_slots):
                    try:
                        changed_signal = getattr(element, property_name + '_changed')
                        changed_signal.connect(changed_slot)
                    except AttributeError:
                        pass

    def _detach_elements(self, elements):
        for element in elements:
            instance_count = self._instance_counts[element] - 1
            assert instance_count >= 0
            if instance_count == 0:
                for property_name, changed_slot in zip(self.property_names, self._property_changed_slots):
                    try:
                        changed_signal = getattr(element, property_name + '_changed')
                        changed_signal.disconnect(changed_slot)
                    except AttributeError:
                        pass
                del self._instance_counts[element]
            else:
                self._instance_counts[element] = instance_count

    def _on_property_changed(self, element, property_name):
        column = self.property_columns[property_name]
        signaling_list = self.signaling_list
        next_idx = 0
        instance_count = self._instance_counts[element]
        assert instance_count > 0
        for _ in range(instance_count):
            row = signaling_list.index(element, next_idx)
            next_idx = row + 1
            self.dataChanged.emit(self.createIndex(row, column), self.createIndex(row, column))

    def _on_inserting(self, idx, elements):
        self.beginInsertRows(Qt.QModelIndex(), idx, idx+len(elements)-1)

    def _on_inserted(self, idx, elements):
        self.endInsertRows()
        self._attach_elements(elements)
        self.dataChanged.emit(self.createIndex(idx, 0), self.createIndex(idx + len(elements) - 1, len(self.property_names) - 1))

    def _on_replaced(self, idxs, replaced_elements, elements):
        self._detach_elements(replaced_elements)
        self._attach_elements(elements)
        self.dataChanged.emit(self.createIndex(min(idxs), 0), self.createIndex(max(idxs), len(self.property_names) - 1))

    def _on_removing(self, idxs, elements):
        self.beginRemoveRows(Qt.QModelIndex(), min(idxs), max(idxs))

    def _on_removed(self, idxs, elements):
        self.endRemoveRows()
        self._detach_elements(elements)
