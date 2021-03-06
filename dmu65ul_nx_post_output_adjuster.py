# Copyright (c) 2019 by Erik Hvatum

from PyQt5 import Qt
import sys
from . import om
from pathlib import Path
import re
from .cnc_program import CncProgram
from .progress_thread_dlg import ProgressThreadDlg

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
                fpath = Path(url.toLocalFile())
                if fpath.exists():
                    self.transform_file(fpath)

    def transform_file(self, fpath):
        cnc_program = CncProgram()
        cnc_program.import_mpf(fpath)
        pt_dlg = ProgressThreadDlg(cnc_program.transform_for_dmu65ul, self)
        pt_dlg.exec()
        if pt_dlg._worker.completed:
            cnc_program.apply_tool_preloading()
            outfn = fpath.name
            # outfn = fpath.stem
            # if outfn[-1] == '_':
            #     outfn = outfn[:-1]
            # else:
            #     outfn = outfn + '_'
            # outfn += '.mpf'
            cnc_program.pattern_ops_across_homes(3)
            cnc_program.export_mpf(fpath.parent / outfn)

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv)
    mw = NxPostOutputAdjuster()
    mw.show()
    app.exec_()
