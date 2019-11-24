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

def with_selected_rows_deletion_shortcut(
        cls,
        desc='Delete selection',
        shortcut=Qt.Qt.Key_Delete,
        shortcut_context=Qt.Qt.WidgetShortcut,
        action_attr_name='delete_selection_action',
        make_handler_method=True,
        handler_method_name='delete_selection',
        connect_action_triggered_to_handler_method=True):
    # Function prototype is included in docstring so that the enum names "Qt.Qt.Key_Delete" and "Qt.Qt.WidgetShortcut" may be
    # seen, rather than their integer values, which they are boiled down to int the function signature known to CPython
    '''with_selected_rows_deletion_shortcut(
        cls,
        desc='Delete selection',
        shortcut=Qt.Qt.Key_Delete,
        shortcut_context=Qt.Qt.WidgetShortcut,
        action_attr_name='delete_selection_action',
        make_handler_method=True,
        handler_method_name='delete_selection',
        connect_action_triggered_to_handler_method=True):

    A class decorator function intended to operate on descendants of QAbstractItemView that adds a delete shortcut and, if
    make_handler_method=False has not been supplied as a decorator argument, a shortcut-triggered handler function.

    The generated shortcut-triggered handler function, named 'delete_section' by default, issues a single delete-slice call for each
    group of adjacent, selected rows.  So, for a QTableView subclass attached to a QAbstractTableModel derivative implemented in
    Python and containing 100k rows, select-all followed by hitting delete may be nearly instantaneous, whereas calling the model's
    removeRow method one hundred thousand times would certainly take a while.

    Ex:
    from PyQt5 import Qt
    from ris_widget import om

    @om.item_view_shortcuts.with_selected_rows_deletion_shortcut
    class LW(Qt.QListWidget): pass

    lw=LW()
    lw.setSelectionMode(Qt.QAbstractItemView.ExtendedSelection)
    lw.addItems(bytearray((c,)).decode('ascii') for c in range('A'.encode('ascii')[0], 'A'.encode('ascii')[0] + 56))
    lw.show()
    # Now, select some items in the list widget that appeared and hit the delete key.'''
    orig_init = cls.__init__
    def init(self, *va, **kw):
        orig_init(self, *va, **kw)
        action = Qt.QAction(self)
        action.setText(desc)
        action.setShortcut(shortcut)
        action.setShortcutContext(shortcut_context)
        self.addAction(action)
        setattr(self, action_attr_name, action)
        if connect_action_triggered_to_handler_method:
            action.triggered.connect(getattr(self, handler_method_name))
    init.__doc__ = orig_init.__doc__
    cls.__init__ = init
    if make_handler_method:
        def on_action_triggered(self):
            sm = self.selectionModel()
            m = self.model()
            if None in (m, sm):
                return
            midxs = sorted(sm.selectedRows(), key=lambda midx: midx.row())
            # "run" as in consecutive indexes specified as range rather than individually
            runs = []
            run_start_idx = None
            run_end_idx = None
            for midx in midxs:
                if midx.isValid():
                    idx = midx.row()
                    if run_start_idx is None:
                        run_end_idx = run_start_idx = idx
                    elif idx - run_end_idx == 1:
                        run_end_idx = idx
                    else:
                        runs.append((run_start_idx, run_end_idx))
                        run_end_idx = run_start_idx = idx
            if run_start_idx is not None:
                runs.append((run_start_idx, run_end_idx))
            for run_start_idx, run_end_idx in reversed(runs):
                m.removeRows(run_start_idx, run_end_idx - run_start_idx + 1)
        setattr(cls, handler_method_name, on_action_triggered)
    return cls
