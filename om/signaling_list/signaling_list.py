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

from abc import ABCMeta
from collections.abc import MutableSequence
from PyQt5 import Qt
import textwrap

class _QtAbcMeta(Qt.pyqtWrapperType, ABCMeta):
    pass

class SignalingList(Qt.QObject, MutableSequence, metaclass=_QtAbcMeta):
    """
    SignalingList: a list-like container representing a collection of objects that
    emits change signals when one or more elements is inserted, removed, or replaced.

    Pre-change signals:
    * inserting(index where objects will be inserted, the objects that will be inserted)
    * removing(indexes of objects to be removed, the objects that will be removed)
    * replacing(indexes of the objects to be replaced, the objects that will be replaced, the objects that will replace them)

    Post-change signals:
    * inserted(index of first inserted object, the objects inserted)
    * removed(former indexes of removed objects, the objects removed)
    * replaced(indexes of the replaced objects, the objects that were replaced, the objects that replaced them)

    The pre-change signals are handy for things like virtual table views that must know of certain changes
    before they occur in order to maintain a consistent state.

    No signals are emitted for objects with indexes that change as a result of inserting or removing
    a preceeding object."""

    inserting = Qt.pyqtSignal(int, list)
    removing = Qt.pyqtSignal(list, list)
    replacing = Qt.pyqtSignal(list, list, list)

    inserted = Qt.pyqtSignal(int, list)
    removed = Qt.pyqtSignal(list, list)
    replaced = Qt.pyqtSignal(list, list, list)

    def __init__(self, iterable=None, parent=None):
        Qt.QObject.__init__(self, parent)
        self.objectNameChanged.connect(self._on_objectNameChanged)
        if iterable is None:
            self._list = list()
        else:
            self._list = list(iterable)

    name_changed = Qt.pyqtSignal(object)
    def _on_objectNameChanged(self):
        self.name_changed.emit(self)
    name = property(
        Qt.QObject.objectName,
        lambda self, name: self.setObjectName('' if name is None else name),
        doc='Property proxy for QObject::objectName Qt property, which is directly accessible via the objectName getter and '
            'setObjectName setter, with change notification signal objectNameChanged.  The proxied change signal, which conforms '
            'to the requirements of ris_widget.om.signaling_list.PropertyTableModel, is name_changed.')

    @staticmethod
    def _obj_repr(obj):
        s = obj.__repr__()
        s = textwrap.indent(s, ' ' * 4)
        return s

    def __repr__(self):
        r = super().__repr__()[:-1]
        if self._list:
            r += '\n[\n' + ',\n'.join(self._obj_repr(obj) for obj in self._list) + '\n]'
        return r + '>'

    def __iter__(self):
        return iter(self._list)

    def __hash__(self):
        # We want this to be hashable even though it's a mutable list.  Same list?  As in,
        # lhs is rhs.  Same hash.  Perfect for our needs.  Equality comparison to verify
        # that a hash collision has not occurred may still go element-wise, which wouldn't
        # be the smartest.
        # TODO: implement __eq__ operator that does "is" before resorting to element-wise.
        # See if doing so makes hashing big signaling lists more efficient.
        return id(self)

    def clear(self):
        'S.clear() -> None -- remove all items from S'
        idxs = list(range(0, len(self._list)))
        objs = list(self._list)
        self.removing.emit(idxs, objs)
        del self._list[:]
        self.removed.emit(idxs, objs)

    def __contains__(self, obj):
        return obj in self._list

    def index(self, value, *va):
        """L.index(value, [start, [stop]]) -> integer -- return first index of value.
        Raises ValueError if the value is not present."""
        return self._list.index(value, *va)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, idx_or_slice):
        return self._list[idx_or_slice]

    def __setitem__(self, idx_or_slice, srcs):
        """Supports the same extended slicing as the list container in Python 3.4.3, including replacement+insertion.
        As with list in Python 3.4.3, trimming of strided slices and replacement of strided slices with simultaneous
        insertion are not supported."""
        if isinstance(idx_or_slice, slice):
            dest_range_tuple = idx_or_slice.indices(len(self._list))
            dest_idxs = list(range(*dest_range_tuple))
            if dest_range_tuple[2] == 1:
                # With stride size of one:
                # * An equal number of sources and destinations results in each destination being replaced by the corresponding source.
                # * An excess of sources as compared to destinations results in replacement of specified destinations with corresponding
                #   sources, with excess sources inserted after the last destination.  If destinations is a zero-width slice such as N:N,
                #   sources are simply inserted at N, increasing the index of the original Nth element by the number of sources specified.
                # * An excess of destinations as compared to sources results in each destination with a corresponding source being
                #   replaced, with excess destinations being deleted.  If the sources iterable is empty, all specified destinations
                #   are deleted, making "S[0:10] = S[0:0]" equivalent to "del S[0:10]".
                srcs_len = len(srcs)
                dests_len = len(dest_idxs)
                common_len = min(srcs_len, dests_len)
                srcs_surplus_len = srcs_len - dests_len
                if common_len > 0:
                    replace_slice = slice(dest_idxs[0], dest_idxs[0]+common_len)
                    replaceds = self._list[replace_slice]
                    replacements = srcs[:common_len]
                    self.replacing.emit(dest_idxs[:common_len], replaceds, replacements)
                    self._list[replace_slice] = srcs[:common_len]
                    self.replaced.emit(dest_idxs[:common_len], replaceds, replacements)
                if srcs_surplus_len > 0:
                    inserts = srcs[common_len:]
                    idx = dest_range_tuple[0] + common_len
                    self.inserting.emit(idx, inserts)
                    self._list[idx:idx] = inserts
                    self.inserted.emit(idx, inserts)
                elif srcs_surplus_len < 0:
                    remove_slice = slice(dest_idxs[common_len], dest_idxs[-1] + 1)
                    self.__delitem__(remove_slice)
            else:
                # Only 1-1 replacement is supported with stride other than one
                if len(dest_idxs) != len(srcs):
                    raise ValueError('attempt to assign sequence of size {} to extended slice of size {}'.format(len(srcs), len(idxs)))
                replaceds = self._list[idx_or_slice]
                self.replacing.emit(dest_idxs, replaceds, srcs)
                self._list[idx_or_slice] = srcs
                self.replaced.emit(dest_idxs, replaceds, srcs)
        else:
            idx = idx_or_slice if idx_or_slice >= 0 else len(self._list) + idx_or_slice
            replaceds = [self._list[idx]]
            self._list[idx] = srcs
            self.replaced.emit([idx], replaceds, [srcs])

    def extend(self, srcs):
        'S.extend(iterable) -- extend sequence by appending elements from the iterable'
        idx = len(self._list)
        srcs = list(srcs)
        self.inserting.emit(idx, srcs)
        self._list.extend(srcs)
        self.inserted.emit(idx, srcs)

    def insert(self, idx, obj):
        'S.insert(index, value) -- insert value before index'
        if idx < 0:
            idx = idx + len(self._list)
        if idx < 0:
            idx = 0
        elif idx > len(self._list):
            idx = len(self._list)
        objs = [obj]
        self.inserting.emit(idx, objs)
        self._list.insert(idx, obj)
        self.inserted.emit(idx, objs)

    def sort(self, key=None, reverse=False):
        self[:] = sorted(self._list, key=key, reverse=reverse)

    def __delitem__(self, idx_or_slice):
        objs = self._list[idx_or_slice]
        if isinstance(idx_or_slice, slice):
            if not objs:
                return
            idxs = list(range(*idx_or_slice.indices(len(self._list))))
        else:
            idxs = [idx_or_slice]
            objs = [objs]
        self.removing.emit(idxs, objs)
        del self._list[idx_or_slice]
        self.removed.emit(idxs, objs)

    def __eq__(self, other):
        try:
            other_len = len(other)
        except TypeError:
            return False
        return len(self) == other_len and all(s == o for s, o in zip(self, other))

    if __debug__:
        @classmethod
        def _test_plain_list_behavior_fidelity(cls, num_iterations=40, stuff_max_len=20, verbose=False):
            """For development and testing purposes, this function performs the same operations on a SignalingList
            and a plain list, and verifies that their contents remain identical.  The operations themselves are
            primarily random extended slicing operations, with the occassional extend call, randomly strided
            delete of a random range, and insert call with a random index and value.  Verbose output for any
            of the three occassional test operations is prepended with a * for visibility."""
            import numpy
            import numpy.random
            from numpy.random import randint as R
            sl = cls()
            l = []
            mb = lambda r: R(len(l)+1) if r else R(-2*len(l)-10, 2*len(l)+10)
            for iteration in range(num_iterations):
                stuff = list(R(1024, size=(R(stuff_max_len),)))
                rb, re = R(2, size=(2,))
                b, e = mb(rb), mb(re)
                if R(2) and b > e:
                    b, e = e, b
                ol = list(l)
                func = R(100)
                if func < 96:
                    l[b:e] = stuff
                    sl[b:e] = stuff
                    if l != sl:
                        raise RuntimeError('{}[{}:{}] = {}:\n{} !=\n{}'.format(ol, b, e, stuff, sl._list, l))
                    if verbose:
                        print('{}[{}:{}] = {}'.format(ol, b, e, stuff))
                elif func < 97:
                    s = (1 if R(3) else -1) * (1 if R(5) else R(5)+1)
                    del l[b:e:s]
                    del sl[b:e:s]
                    if l != sl:
                        raise RuntimeError('del {}[{}:{}:{}]:\n{} !=\n{}'.format(ol, b, e, s, sl._list, l))
                    if verbose:
                        print('* del {}[{}:{}:{}]'.format(ol, b, e, s))
                elif func < 98:
                    l.extend(stuff)
                    sl.extend(stuff)
                    if l != sl:
                        raise RuntimeError('{}.extend({}):\n{} !=\n{}'.format(ol, stuff, sl._list, l))
                    if verbose:
                        print('* {}.extend({})'.format(ol, stuff))
                else:
                    stuff = R(1024)
                    l.insert(b, stuff)
                    sl.insert(b, stuff)
                    if l != sl:
                        raise RuntimeError('{}.insert({}, {}):\n{} !=\n{}'.format(ol, b, stuff, sl._list, l))
                    if verbose:
                        print('* {}.insert({}, {})'.format(ol, b, stuff))
