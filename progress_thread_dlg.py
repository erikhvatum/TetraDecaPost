# Copyright (c) 2019 by Erik Hvatum

from PyQt5 import Qt

class _Worker(Qt.QObject):
    completion_updated = Qt.pyqtSignal(float)

    def __init__(self, generator_func):
        super().__init__()
        self.completed = False
        self.generator_func = generator_func
        self.cancel = False

    @Qt.pyqtSlot()

    def proc(self):
        try:
            self.completed = False
            if self.cancel:
                self.cancel
            for c in self.generator_func():
                if self.cancel:
                    return
                self.completion_updated.emit(c)
            self.completed = True
        finally:
            self.thread().quit()

class ProgressThreadDlg(Qt.QProgressDialog):
    _start_worker = Qt.pyqtSignal()
    _MIN, _MAX = 0.0, 10000.0
    def __init__(self, generator_func, parent):
        super().__init__(parent)
        self._worker = _Worker(generator_func)
        self._thread = Qt.QThread()
        self._worker.moveToThread(self._thread)
        self._worker.completion_updated.connect(self._on_completion_updated)
        self._start_worker.connect(self._worker.proc)
        self.canceled.connect(self._on_canceled)
        self._thread.finished.connect(self.accept)
        self._thread.start()
    
    def _on_canceled(self):
        self._worker.cancel = True

    @Qt.pyqtSlot(float)
    def _on_completion_updated(self, c):
        self.setValue(int(round((self._MAX - self._MIN)*c + self._MIN)))

    def exec(self):
        self._start_worker.emit()
        # self._thread.quit()
        return super().exec()
