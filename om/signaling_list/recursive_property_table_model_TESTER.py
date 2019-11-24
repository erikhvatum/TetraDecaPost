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
from .recursive_property_table_model import RecursivePropertyTableModel
from .signaling_list import SignalingList
from ..property import Property

class A(Qt.QObject):
    changed = Qt.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        for property in self.properties:
            property.instantiate(self)

    properties = []

    a = Property(properties, 'a', default_value_callback=lambda _: 'default a')
    b = Property(properties, 'b', default_value_callback=lambda _: 'default b')
    c = Property(properties, 'c', default_value_callback=lambda _: 'default c')
    d = Property(properties, 'd', default_value_callback=lambda _: 'default d')
    e = Property(properties, 'e', default_value_callback=lambda _: 'default e')

    for property in properties:
        exec(property.changed_signal_name + ' = Qt.pyqtSignal(object)')
    del property

class TestModel(RecursivePropertyTableModel):
    def flags(self, midx):
        f = super().flags(midx)
        if f & Qt.Qt.ItemIsEnabled:
            f |= Qt.Qt.ItemIsEditable
        return f

class TestWidget(Qt.QWidget):
    def __init__(self, window_title=None):
        super().__init__()
        if window_title is None:
            window_title = __file__
        self.setWindowTitle(window_title)
        self.gvs = set()
        vl = Qt.QVBoxLayout()
        self.setLayout(vl)
        self.table = Qt.QTableView()
        self.table.horizontalHeader().setSectionResizeMode(Qt.QHeaderView.ResizeToContents)
        vl.addWidget(self.table)
        hl = Qt.QHBoxLayout()
        vl.addLayout(hl)
        for test_index in range(99999):
            test_fn_name = '_test_{}'.format(test_index)
            if hasattr(self, test_fn_name):
                btn = Qt.QPushButton(str(test_index))
                btn.clicked.connect(getattr(self, test_fn_name))
                hl.addWidget(btn)
            else:
                break
        hl = Qt.QHBoxLayout()
        self.desc_graph_button = Qt.QPushButton('desc tree')
        self.desc_graph_button.clicked.connect(self._on_desc_graph_button_clicked)
        hl.addWidget(self.desc_graph_button)
        self.inst_graph_button = Qt.QPushButton('inst tree')
        self.inst_graph_button.clicked.connect(self._on_inst_graph_button_clicked)
        hl.addWidget(self.inst_graph_button)
        vl.addLayout(hl)
        self.signaling_list = SignalingList()
        self.model = TestModel(
            (
                'a',
                'a.a',
                'a.b','a.b.c','a.b.c.d','a.b.c.d.e',
                'a.c',
                'a.d',
                'a.e',
                'b.a',
                'b.b',
                'b.c',
                'b.d',
                'b.e',
                'c.a',
                'c.b',
                'c.c',
                'c.d',
                'c.e',
                'd.a',
                'd.b',
                'd.c',
                'd.d',
                'd.e',
                'e.a',
                'e.b',
                'e.c',
                'e.d',
                'e.e'
            ),
            self.signaling_list)
        self.table.setModel(self.model)

    def _test_0(self):
        self.signaling_list.append(A())
        self.signaling_list[-1].a = A()
        self.signaling_list[-1].a.a = 'stuff'

    def _test_1(self):
        self.signaling_list.append(A())
        self.signaling_list[-1].a = A()
        self.signaling_list[-1].b = A()
        self.signaling_list[-1].c = A()
        self.signaling_list[-1].d = A()
        self.signaling_list[-1].e = A()
        self.signaling_list.append(self.signaling_list[-1])
        self.signaling_list.append(A())
        self.signaling_list[-1].a = A()
        self.signaling_list[-1].b = A()
        self.signaling_list[-1].c = A()
        self.signaling_list[-1].d = A()
        self.signaling_list[-1].e = A()
        self.signaling_list[-1].a.a = 21
        self.signaling_list[-1].a.b = A()
        self.signaling_list[-1].a.b.c = A()
        self.signaling_list[-1].a.b.c.d = A()
        self.signaling_list[-1].a.b.c.d.e = 42

    def _on_desc_graph_button_clicked(self):
        self._show_dot_graph(self.model._property_descr_tree_root.dot_graph, '.model._property_descr_tree_root.dot_graph')

    def _on_inst_graph_button_clicked(self):
        self._show_dot_graph(self.model._property_inst_tree_root.dot_graph, '._property_inst_tree_root.dot_graph')

    def _show_dot_graph(self, dot, name):
        import io
        import pygraphviz
        gs = Qt.QGraphicsScene(self)
        gv = GV(gs)
        self.gvs.add(gv)
        gv.closing_signal.connect(lambda: self.gvs.remove(gv))
        im = Qt.QImage.fromData(
            pygraphviz.AGraph(string=dot, directed=True).draw(format='png', prog='dot'),
            'png')
        gs.addPixmap(Qt.QPixmap.fromImage(im))
        gv.setDragMode(Qt.QGraphicsView.ScrollHandDrag)
        gv.setBackgroundBrush(Qt.QBrush(Qt.Qt.black))
        gv.setWindowTitle(name)
        gv.show()

class GV(Qt.QGraphicsView):
    closing_signal = Qt.pyqtSignal()

    def closeEvent(self, event):
        self.closing_signal.emit()
        super().closeEvent(event)

    def wheelEvent(self, event):
        zoom = self.transform().m22()
        original_zoom = zoom
        increments = event.angleDelta().y() / 120
        if increments > 0:
            zoom *= 1.25**increments
        elif increments < 0:
            zoom *= 0.8**(-increments)
        else:
            return
        if zoom < 0.167772:
            zoom = 0.167772
        elif zoom > 18.1899:
            zoom = 18.1899
        elif abs(abs(zoom)-1) < 0.1:
            zoom = 1
        scale_zoom = zoom / original_zoom
        self.setTransformationAnchor(Qt.QGraphicsView.AnchorUnderMouse)
        self.scale(scale_zoom, scale_zoom)

if __name__ == '__main__':
    import sys
    app = Qt.QApplication(sys.argv)
    test_widget = TestWidget()
    test_widget.show()
    app.exec_()
