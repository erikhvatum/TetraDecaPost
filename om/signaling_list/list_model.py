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

from PyQt5 import Qt

class ListModel(Qt.QAbstractListModel):
    """ListModel: Glue for attaching a Qt.QListView (or similar) to a SignalingList such that the elements the
    SignalingList are shown as rows containing a representation of either a specified attribute/property of
    each element or the element itself.  If a string is supplied for property_name, the value of the named
    attribute/property is used.  If None is supplied for property_name, the element itself is used.

    What is meant by "used"?   When it needs to draw a row, Qt.QTableView constructs a Qt.QModelIndex pointing
    to that row in its model.  Qt.QTableView then calls the paint method of delegate for that row with the
    Qt.QModelIndex as an argument.  The default delegate, which is used unless another has been specified
    for the Qt.QTableView row (or all rows), retrieves the data to be presented in the row by calling the Qt.QModelIndex's
    data(..) function with Qt.Qt.DisplayRole as an argument.  This, in turn, calls the Qt.QTableView model's
    .data(..) function with the Qt.QModelIndex and Qt.Qt.DisplayRole as arguments.

    So, if Qt.QTableView's model is a ListModel, our .data(..) function is called.  As can be seen in the
    definition of the data method below, the value (whether element attribute/property value or the value of the
    element itself) is wrapped in a Qt.QVariant and returned.

    Qt.QVariant is a simple C++ container storing a void pointer, enum type ID, and integer user-defined-type
    ID (for non user-defined types, ie types with built-in Qt support, the enum and integer member variable values
    are the same).  In C++, where the return type of a function can not depend on the value of a function's
    argument, the value represented by a QVariant must be extracted by using the appropriate member function.
    For example, if QVariant instance q stores a list, q.toList().

    However, Python does not impose any such constraint, and so PyQt offers only one Qt.QVariant data
    extraction method: value.  Qt.QVariant.value(..) calls the appropriate QVariant::to* function for
    Qt.QVariant.type(..) and returns the result.  If Qt.QVariant.type(self) and Qt.QVariant.userType(..)
    are both a particular magic value, PyQt treats the contained void pointer as a Py_Object*, incrementing
    the object's reference count upon construction, decrementing it upon deletion, and returning the Python
    object in response to .value(..).

    The default delegate understands only a subset of the types with built-in QVariant support, including str,
    int, and float.  Rows with unsupported values are appear to be empty.  If a row's value is of supported
    type, an appropriate widget is presented when the row is edited in the GUI.  If editing completes successfully,
    the new value is of the same type as the original, and this new value is wrapped in a Qt.QVariant and passed
    to the model's setData method along with the model index of the row edited and Qt.Qt.EditRole."""

    def __init__(self, property_name=None, signaling_list=None, parent=None):
        super().__init__(parent)
        self._signaling_list = None
        self.property_name = property_name
        if property_name is not None:
            # Attempting to count instances of an immutable per row can lead to trouble, as two "1" values 
            # may appear to share the same object although the two list elements are not otherwise related.
            # The apparent sharing is an artifact of the CPython's implementation.
            self._instance_counts = {}
        self.signaling_list = signaling_list

    def rowCount(self, _=None):
        sl = self.signaling_list
        return 0 if sl is None else len(sl)

    def columnCount(self, _=None):
        return 1

    def flags(self, midx):
        f = Qt.Qt.ItemIsSelectable | Qt.Qt.ItemNeverHasChildren
        if midx.isValid():
            f |= Qt.Qt.ItemIsEnabled | Qt.Qt.ItemIsEditable
        f |= self.drag_drop_flags(midx)
        return f

    def drag_drop_flags(self):
        return 0

    def get_row(self, row):
        element = self.signaling_list[row]
        pn = self.property_name
        if pn is None:
            return element
        return getattr(element, pn, None)

    def data(self, midx, role=Qt.Qt.DisplayRole):
        if midx.isValid() and role in (Qt.Qt.DisplayRole, Qt.Qt.EditRole):
            return Qt.QVariant(self.get_row(midx.row()))
        return Qt.QVariant()

    def set_row(self, row, v):
        pn = self.property_name
        if pn is None:
            self.signaling_list[row] = v
        else:
            setattr(self.signaling_list[row], pn, v)

    def setData(self, midx, value, role=Qt.Qt.EditRole):
        if midx.isValid() and role == Qt.Qt.EditRole:
            if isinstance(value, Qt.QVariant):
                value = value.value()
            self.set_row(midx.row(), value)
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
                    assert self.property_name is None or len(self._instance_counts) == 0
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
        pname = self.property_name
        if pname is None:
            return
        csn = pname + '_changed'
        for element in elements:
            instance_count = self._instance_counts.get(element, 0) + 1
            assert instance_count > 0
            self._instance_counts[element] = instance_count
            if instance_count == 1:
                try:
                    getattr(element, csn).connect(self._on_property_changed)
                except AttributeError:
                    pass

    def _detach_elements(self, elements):
        pname = self.property_name
        if pname is None:
            return
        csn = pname + '_changed'
        for element in elements:
            instance_count = self._instance_counts[element] - 1
            assert instance_count >= 0
            if instance_count == 0:
                try:
                    getattr(element, csn).disconnect(self._on_property_changed)
                except AttributeError:
                    pass
                del self._instance_counts[element]
            else:
                self._instance_counts[element] = instance_count

    def _on_property_changed(self, element):
        sl = self.signaling_list
        next_row = 0
        instance_count = self._instance_counts[element]
        assert instance_count > 0
        for _ in range(instance_count):
            row = sl.index(element, next_row)
            next_row = row + 1
            self.dataChanged.emit(self.createIndex(row, 0), self.createIndex(row, 0))

    def _on_inserting(self, idx, elements):
        self.beginInsertRows(Qt.QModelIndex(), idx, idx+len(elements)-1)

    def _on_inserted(self, idx, elements):
        self.endInsertRows()
        self._attach_elements(elements)

    def _on_replaced(self, idxs, replaced_elements, elements):
        self._detach_elements(replaced_elements)
        self._attach_elements(elements)
        self.dataChanged.emit(self.createIndex(min(idxs), 0), self.createIndex(max(idxs), 0))

    def _on_removing(self, idxs, elements):
        self.beginRemoveRows(Qt.QModelIndex(), min(idxs), max(idxs))

    def _on_removed(self, idxs, elements):
        self.endRemoveRows()
        self._detach_elements(elements)
