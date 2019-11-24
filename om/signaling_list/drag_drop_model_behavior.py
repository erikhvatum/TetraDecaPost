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
from pathlib import Path
from PyQt5 import Qt
import sys

# Everything in this file could be generalized into supporting row-wise and column-wise tables generally and dragging
# between the two, but we haven't needed that.  Additionally, generalization away from .signaling_list is possible,
# but we haven't needed that, either.

# Packed ROWS_DRAG_MIME_TYPE data consists of a uint64 that is the sending model's Python id() followed by zero or
# more int64, uint64 pairs that are the row (an offset into a signaling_list) and value of the element represented
# by that row (.signaling_list[row]).
ROWS_DRAG_MIME_TYPE = 'application/x-dragged_rows_ZL1AO5IENFKSK9BQP0'

class RowsDrag:
    __slots__ = ('src_model', 'rows')
    def __init__(self, src_model, rows):
        self.src_model = src_model
        self.rows = rows

class DragDropModelBehavior:
    """DragDropModelBehavior: A mix-in for adding basic row-wise drag-and-drop behavior to any derivative of
    Qt.QAbstractItemModel."""
    def supportedDropActions(self):
#       print('DragDropModelBehavior supportedDropActions')
        return Qt.Qt.CopyAction | Qt.Qt.LinkAction

    def supportedDragActions(self):
#       print('DragDropModelBehavior supportedDragActions')
        return Qt.Qt.LinkAction

    def canDropMimeData(self, mime_data, drop_action, row, column, parent):
#       print('mime_data.formats()', mime_data.formats())
        rows_drag = self._decode_rows_drag_mime_data(mime_data)
#       print('canDropMimeData(self, rows_drag={}, drop_action={}, row={}, column={}, parent={})'.format('' if rows_drag is None else rows_drag.rows, drop_action, row, column, parent))
        if rows_drag is not None and len(rows_drag.rows) > 0:
            return self.can_drop_rows(rows_drag.src_model, rows_drag.rows, row, column, parent)
        if mime_data.hasImage():
            url = mime_data.urls()[0].toDisplayString() if mime_data.hasUrls() else None
            return self.can_drop_qimage(mime_data.imageData(), url, row, column, parent)
        if mime_data.hasUrls():
            # Note: if the URL is a "file://..." representing a local file, toLocalFile returns a string
            # appropriate for feeding to Python's open() function.  If the URL does not refer to a local file,
            # toLocalFile returns None.
            fpaths = [url.toLocalFile() for url in mime_data.urls()]
            if sys.platform == 'darwin' and len(fpaths) > 0 and fpaths[0].startswith('file:///.file/id='):
                e = 'In order for image file drag & drop to work on OS X >=10.10 (Yosemite), please upgrade to at least Qt 5.4.1.'
                Qt.QMessageBox.information(None, 'Qt Upgrade Required', e)
                return False
            return self.can_drop_files(fpaths, row, column, parent)
        if mime_data.hasText():
            return self.can_drop_text(mime_data.text(), row, column, parent)
        return False

    def dropMimeData(self, mime_data, drop_action, row, column, parent):
#       print('dropMimeData mime_data.hasImage()', mime_data.hasImage())
        rows_drag = self._decode_rows_drag_mime_data(mime_data)
        if rows_drag is not None and len(rows_drag.rows) > 0:
            return self.handle_dropped_rows(rows_drag.src_model, rows_drag.rows, row, column, parent)
        if mime_data.hasImage():
            url = mime_data.urls()[0].toDisplayString() if mime_data.hasUrls() else None
            return self.handle_dropped_qimage(mime_data.imageData(), url, row, column, parent)
        if mime_data.hasUrls():
            # Note: if the URL is a "file://..." representing a local file, toLocalFile returns a string
            # appropriate for feeding to Python's open() function.  If the URL does not refer to a local file,
            # toLocalFile returns None.
            fpath_strs = [url.toLocalFile() for url in mime_data.urls()]
            if sys.platform == 'darwin' and any(fpath_str.startswith('file:///.file/id=') for fpath_str in fpath_strs):
                e = 'In order for image file drag & drop to work on OS X >=10.10 (Yosemite), please upgrade to at least Qt 5.4.1.'
                Qt.QMessageBox.information(None, 'Qt Upgrade Required', e)
                return False
            return self.handle_dropped_files([Path(fpath_str) for fpath_str in fpath_strs], row, column, parent)
        if mime_data.hasText():
            return self.handle_dropped_text(mime_data.text(), row, column, parent)
        return False

    def drag_drop_flags(self, midx):
        # NB: drag_drop_flags_transform(..) is called by the flags method of om.signaling_list.*model instances.  Such a flags
        # method either directly or indirectly overrides QAbstractItemView.flags(..).
        #
        # QAbstractItemView and derivatives call their model's flags method to determine if an item at a specific model index
        # ("midx") can be dragged about or dropped upon.  If midx is valid, flags(..) is being called for an existing row, and
        # we respond that it is draggable.  If midx is not valid, flags(..) is being called for an imaginary row between two
        # existing rows or at the top or bottom of the table, all of which are valid spots for a row to be inserted, so we
        # respond that the imaginary row in question is OK to drop upon.
        return Qt.Qt.ItemIsDragEnabled if midx.isValid() else Qt.Qt.ItemIsDropEnabled

    def can_drop_qimage(self, qimage, name, dst_row, dst_column, dst_parent):
        return not qimage.isNull()

    def can_drop_files(self, fpaths, dst_row, dst_column, dst_parent):
        return True

    def can_drop_rows(self, src_model, src_rows, dst_row, dst_column, dst_parent):
        return True

    def can_drop_text(self, text, dst_row, dst_column, dst_parent):
        return True

    def handle_dropped_qimage(self, qimage, name, dst_row, dst_column, dst_parent):
#       print('handle_dropped_qimage(self, qimage={}, name={}, dst_row={}, dst_column={}, dst_parent={})'.format(qimage, name, dst_row, dst_column, dst_parent))
        return False

    def handle_dropped_files(self, fpaths, dst_row, dst_column, dst_parent):
        return False

    def handle_dropped_rows(self, src_model, src_rows, dst_row, dst_column, dst_parent):
        d_sl, s_sl = self.signaling_list, src_model.signaling_list
        elements = [s_sl[src_row] for src_row in src_rows]
        if self.should_delete_rows_dragged_from_source(src_model):
            orig_src_midxs = [Qt.QPersistentModelIndex(src_model.createIndex(src_row, 0)) for src_row in reversed(src_rows)]
            d_sl[dst_row:dst_row] = elements
            for orig_src_midx in orig_src_midxs:
                del s_sl[orig_src_midx.row()]
        else:
            d_sl[dst_row:dst_row] = elements
        return True

    def should_delete_rows_dragged_from_source(self, src_model):
        # Called by the various handle_dropped_* methods in order to determine whether the rows dropped should be removed
        # from their origin model.
        #
        # The default behavior implemented in the following line of code: Dropping a row onto this model inserts that row.
        # If the row originated from the same model into which it is dropped, we return True in order that the source row
        # is deleted, causing an intra-model drag to appear to be a re-ordering operation / move.
        return src_model is self

    def _decode_rows_drag_mime_data(self, mime_data):
        """If mime_data contains packed ROWS_DRAG_MIME_TYPE mime data, it is unpacked into a list containing the source model
        and objects dragged, and this tuple is returned.  None is returned otherwise."""
        if mime_data.hasFormat(ROWS_DRAG_MIME_TYPE):
            d = mime_data.data(ROWS_DRAG_MIME_TYPE)
            ds = Qt.QDataStream(d, Qt.QIODevice.ReadOnly)
            rows = []
            src_model = ctypes.cast(ds.readUInt64(), ctypes.py_object).value
            while not ds.atEnd():
                rows.append(ds.readInt64())
            if rows:
                return RowsDrag(src_model, rows)

    def handle_dropped_text(self, text, dst_row, dst_column, dst_parent):
        return False

    def mimeTypes(self):
        return ['application/x-qabstractitemmodeldatalist', 'application/x-qt-image', ROWS_DRAG_MIME_TYPE]

    def mimeData(self, midxs):
        mime_data = super().mimeData(midxs)
        if mime_data is None:
            mime_data = Qt.QMimeData()
        d = Qt.QByteArray()
        ds = Qt.QDataStream(d, Qt.QIODevice.WriteOnly)
        ds.writeUInt64(id(self))
        # There is an midx for every column of the dragged row(s), but our ROW_DRAG_MIME_TYPE data should contain only one entry per row
        packed_rows = set()
        for midx in midxs:
            assert midx.isValid()
            row = midx.row()
            if row in packed_rows:
                continue
            packed_rows.add(row)
            ds.writeInt64(row)
        mime_data.setData(ROWS_DRAG_MIME_TYPE, d)
        return mime_data
