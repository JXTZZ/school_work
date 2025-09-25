from typing import List, Tuple
from PyQt5.QtCore import QThread, pyqtSignal
from .engine import WatermarkSettings, ExportSettings, export_image

class ExportWorker(QThread):
    progress = pyqtSignal(int, int, str, bool, str)  # current, total, path, ok, message_or_out
    finished = pyqtSignal(int, int)  # success_count, total

    def __init__(self, files: List[str], wm: WatermarkSettings, exp: ExportSettings):
        super().__init__()
        self.files = files
        self.wm = wm
        self.exp = exp
        self._success = 0

    def run(self):
        total = len(self.files)
        self._success = 0
        for idx, p in enumerate(self.files, start=1):
            ok, out = export_image(p, self.wm, self.exp)
            if ok:
                self._success += 1
            self.progress.emit(idx, total, p, ok, out)
        self.finished.emit(self._success, total)

    def success_count(self) -> int:
        return self._success

