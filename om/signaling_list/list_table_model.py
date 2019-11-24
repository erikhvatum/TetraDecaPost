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

class ListTableModel(Qt.QAbstractTableModel):
    """Glue for presenting a list of lists as a table whose rows are outer list elements, first column
    is specified inner list property (typically "name"), and remaining columns are inner list elements."""

    def __init__(self, element_property_name='name', element_element_property_name=None, signaling_list=None, parent=None):
        """element_property_name: The name of the property or attribute of self._signaling_list[r] to show
        in row r, column 0.
        element_element_property_name: The name of the property or attribute of self._signaling_list[r].signaling_list[n]
        to show in row r, column n+1."""
        super().__init__(parent)
        self._signaling_list = None
        self.element_property_name = element_property_name
        self.element_element_property_name = element_element_property_name
        self._element_inst_nodes = {}
        # _el_to_ein: Element Length to Element Inst Node, where element length is
        # len(ListTableModel_instance.signaling_list[row].signaling_list)
        self._el_to_ein = {}
        self.signaling_list = signaling_list

    def rowCount(self, _=None):
        sl = self.signaling_list
        return 0 if sl is None else len(sl)

    def columnCount(self, _=None):
        return self._max_ein_width + 1

    def flags(self, midx):
        f = Qt.Qt.ItemIsSelectable | Qt.Qt.ItemNeverHasChildren
        if midx.isValid():
            row = midx.row()
            if row <= len(self.signaling_list[row]):
                f |= Qt.Qt.ItemIsEnabled
        f |= self.drag_drop_flags(midx)
        return f

    def drag_drop_flags(self, midx):
        return 0

    def data(self, midx, role=Qt.Qt.DisplayRole):
        if midx.isValid() and role in (Qt.Qt.DisplayRole, Qt.Qt.EditRole):
            column = midx.column()
            if column == 0:
                return Qt.QVariant(getattr(self.signaling_list[midx.row()], self.element_property_name))
            if self.element_element_property_name is None:
                return Qt.QVariant(self.signaling_list[midx.row()].signaling_list[column-1])
            return Qt.QVariant(getattr(self.signaling_list[midx.row()].signaling_list[column-1], self.element_element_property_name))
        return Qt.QVariant()

    def setData(self, midx, v, role=Qt.Qt.EditRole):
        if midx.isValid() and role == Qt.Qt.EditRole:
            column = midx.column()
            if column == 0:
                setattr(self.signaling_list[midx.row()], self.element_property_name, v)
            else:
                if self.element_element_property_name is None:
                    self.signaling_list[midx.row()].signaling_list[column-1] = v
                else:
                    setattr(self.signaling_list[midx.row()].signaling_list[column-1], self.element_element_property_name, v)
            return True
        return False

    def headerData(self, section, orientation, role=Qt.Qt.DisplayRole):
        if role == Qt.Qt.DisplayRole:
            if orientation == Qt.Qt.Vertical:
                if 0 <= section < self.rowCount():
                    return Qt.QVariant(section)
            if orientation == Qt.Qt.Horizontal:
                if section == 0:
                    return Qt.QVariant(self.element_property_name)
                if section < self.columnCount():
                    r = '[{}]'.format(section - 1)
                    if self.element_element_property_name is not None:
                        r += '.{}'.format(self.element_element_property_name)
                    return Qt.QVariant(r)
        return Qt.QVariant()

    def removeRows(self, row, count, parent=Qt.QModelIndex()):
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

    def _attach_elements(self, es):
        for e in es:
            if e not in self._element_inst_nodes:
                ein = self._element_inst_nodes[e] = _ElementInstNode(self, e)
            else:
                ein = self._element_inst_nodes.get()
                ein.eic += 1
            assert ein.eic > 0


    def _detach_elements(self, es):
        for e in es:
            ein = self._element_inst_nodes[e]
            ein.eic -= 1
            assert ein.eic >= 0
            if ein.eic == 0:
                self._max_width_eins.remove(ein)
                # TODO: 

    def _on_element_property_changed(self, element):
        sl = self.signaling_list
        next_idx = 0
        instance_count = self._element_micro_models[element].element_instance_count
        assert instance_count > 0
        for _ in range(instance_count):
            row = sl.index(element, next_idx)
            next_idx = row + 1
            self.dataChanged.emit(self.createIndex(row, 0), self.createIndex(row, 0))

    def _on_inserting(self, idx, elements):
        pass

    def _on_inserted(self, idx, elements):
        pass

    def _on_replaced(self, idx, replaced_elements, elements):
        pass

    def _on_removing(self, idxs, elements):
        pass

    def _on_removed(self, idxs, elements):
        pass

    def _on_ees_changed(self, e, ee, eeidxs):
        sl = self.signaling_list
        next_eidx = 0
        eic = self._element_inst_nodes[e].eic
        assert eic > 0
        for _ in range(eic):
            eidx = sl.index(e, next_eidx)
            next_eidx = eidx + 1
            for eeidx in eeidxs:
                self.dataChanged.emit(self.createIndex(idx, eeidx+1), self.createIndex(row, eeidx+1))

    def _on_ees_inserting(self, ein, idx, ees):
        self.beginInsertRows(Qt.QModelIndex(), )

    def _on_ees_inserted(self, ein, idx, ees):
        pass

    def _on_ees_replaced(self, ein, idxs, replaced_ees, ees):
        pass

    def _on_ees_removing(self, ein, idxs, ees):
        pass

    def _on_ees_removed(self, ein, idxs, ees):
        pass

class _ElementInstNode(Qt.QObject):
    ees_changed = Qt.pyqtSignal(object, object, idxs)
    ees_inserting = Qt.pyqtSignal(object, int, list)
    ees_inserted = Qt.pyqtSignal(object, int, list)
    ees_replaced = Qt.pyqtSignal(object, list, list, list)
    ees_removing = Qt.pyqtSignal(object, list, list)
    ees_removed = Qt.pyqtSignal(object, list, list)

    def __init__(self, element, element_instance_count=1, element_element_property_name=None):
        super().__init__()
        # len: maintained by ListTableModel, _ElementInstNode.len represents ListTableModel's concept of
        # len(_ElementInstNode.e.signaling_list), which will be out of date during _ElementInstNode
        # construction and when _ElementInstNode._on_inserted(..) and _ElementInstNode._on_removed(..)
        # are called.
        self.len = None
        self.eepn = element_element_property_name # eepn: "Element Element Property Name"
        if self.eepn is not None:
            self.eepcsn = self.eepn + '_changed' # eepcsn: "Element Element Property Change Signal Name"
            # NB: If there is no element element property name, it is because table cells beyond column 0
            # are to be filled with str(element_element) and not element_element."property_name".  An
            # element element to be rendered directly as its own stringification may therefore be a Python
            # immutable such as an int.  Attempting to count instances of an immutable per row can lead
            # to trouble, as two "1" values may appear to share the same object although the two list elements
            # are not otherwise related.  The apparent sharing is an artifact of the CPython's implementation.
            self.eeics = {} # eeics: "Element Element Instance CountS"
        self.e = element
        self.eic = element_instance_count #eic: "Element Instance Count"
        sl = element.signaling_list
        sl.inserting.connect(self._on_inserting)
        sl.inserted.connect(self._on_inserted)
        sl.replaced.connect(self._on_replaced)
        sl.removing.connect(self._on_removing)
        sl.removed.connect(self._on_removed)
        self._attach_ees(sl)

    def detach_e(self):
        sl = self.e.signaling_list
        self._detach_ees(sl)
        assert self.eic == 0
        sl.inserting.disconnect(self._on_inserting)
        sl.inserted.disconnect(self._on_inserted)
        sl.replaced.disconnect(self._on_replaced)
        sl.removing.disconnect(self._on_removing)
        sl.removed.disconnect(self._on_removed)
        del self.e

    def _attach_ees(self, ees):
        for ee in ees:
            eeic = self.eeics.get(ee, 0) + 1
            assert eeic > 0
            self.eeics[ee] = eeic
            if eeic == 1 and self.eepn is not None:
                try:
                    eecs = getattr(ee, self.eepcsn)
                    eecs.connect(self._on_property_changed)
                except AttributeError:
                    pass

    def _detach_ees(self, ees):
        for ee in ees:
            eeic = self.eeics[ee] - 1
            assert eeic >= 0
            if eeic == 0:
                if self.eepn is not None:
                    try:
                        eecs = getattr(ee, self.eepcsn)
                        eecs.disconnect(self._on_property_changed)
                    except AttributeError:
                        pass
                del self.eeics[ee]
            else:
                self.eeics[ee] = eeic

    def _on_property_changed(self, ee):
        sl = self.e.signaling_list
        assert ee in sl
        next_idx = 0
        eeic = self.eeics[ee]
        assert eeic > 0
        idxs = []
        for _ in range(eeic):
            idx = sl.index(ee, next_idx)
            next_idx = idx + 1
            idxs.append(idx)
        self.ees_changed.emit(self, ee, idxs)

    def _on_inserting(self, idx, ees):
        self.ees_inserting.emit(self, idx, ees)

    def _on_inserted(self, idx, ees):
        self._attach_ees(ees)
        self.ees_inserted.emit(self, idx, ees)

    def _on_replaced(self, idxs, replaced_ees, ees):
        self._detach_ees(replaced_ees)
        self._attach_ees(ees)
        self.ees_replaced.emit(self, idxs, replaced_ees, ees)

    def _on_removing(self, idxs, ees):
        self.ees_removing.emit(self, idxs, ees)

    def _on_removed(self, idxs, ees):
        self._detach_ees(ees)
        self.ees_removed.emit(self, idxs, ees)
