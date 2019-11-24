#!/usr/bin/env python3

from PyQt5 import Qt
import sys
from . import om
from pathlib import Path
from .cnc_program import CncProgram

class NxPostOutputAdjuster(Qt.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('DMU65 NX Post Output Adjuster')
        self.setAcceptDrops(True)
        self._cnc_program = None

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                fpath = Path(url.path())
                if fpath.exists():
                    self.transform_file(fpath)

    def transform_file(self, fpath):
        cnc_program = CncProgram()
        cnc_program.import_mpf(fpath)
        cnc_program.transform_for_dmu65ul()
        cnc_program.export_mpf(fpath.parent / (fpath.stem + '_.mpf'))

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv)
    mw = NxPostOutputAdjuster()
    mw.show()
    app.exec_()
