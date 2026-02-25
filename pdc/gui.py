"""PyQt GUI for Pioneer DJ Corrector."""

import time

from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdc.processor import process
from pdc.usb import get_display_strings, parse_mountpoint_from_display

STATUS_COLORS = {
    "ok": QColor(220, 255, 220),
    "cached": QColor(200, 255, 200),
    "needs_fix": QColor(255, 255, 180),
    "needs_convert": QColor(255, 230, 150),
    "fixed": QColor(150, 255, 150),
    "converted": QColor(120, 255, 120),
    "will_not_fix": QColor(255, 180, 180),
    "failed": QColor(255, 120, 120),
}

def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)} sec"
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}" if m < 60 else f"{m} min {s} sec"


STATUS_LABELS = {
    "ok": "OK",
    "cached": "OK (cached)",
    "needs_fix": "Needs header fix",
    "needs_convert": "Needs conversion",
    "fixed": "Fixed",
    "converted": "Converted",
    "will_not_fix": "Will not fix",
    "failed": "Failed",
}


class ProcessWorker(QThread):
    status = pyqtSignal(str)
    progress = pyqtSignal(str, int, int, str)
    file_status = pyqtSignal(str, str, str)

    def __init__(self, usb_drive: str) -> None:
        super().__init__()
        self._usb_drive = usb_drive

    def run(self) -> None:
        def on_status(msg: str) -> None:
            self.status.emit(msg)

        def on_progress(phase: str, current: int, total: int, desc: str) -> None:
            self.progress.emit(phase, current, total, desc)

        def on_file(rel: str, status: str, error_msg: str) -> None:
            self.file_status.emit(rel, status, error_msg)

        process(
            self._usb_drive,
            on_status=on_status,
            on_progress=on_progress,
            on_file=on_file,
        )
        self.status.emit("Complete.")


class PioneerDJCorrectorApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Pioneer DJ Corrector")
        self.setMinimumSize(500, 450)
        self.resize(500, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._combo = QComboBox()
        self._combo.setEditable(False)
        self._combo.addItem("Select USB Drive")
        layout.addWidget(self._combo)

        self._convert_btn = QPushButton("Convert")
        self._convert_btn.clicked.connect(self._on_convert)
        layout.addWidget(self._convert_btn)

        self._operation_label = QLabel("")
        layout.addWidget(self._operation_label)

        self._progress = QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        self._progress.setTextVisible(True)
        layout.addWidget(self._progress)

        self._file_list = QListWidget()
        self._file_list.setAlternatingRowColors(False)
        layout.addWidget(self._file_list)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        self._worker: ProcessWorker | None = None
        self._file_items: dict[str, QListWidgetItem] = {}
        self._elapsed_timer: QTimer | None = None
        self._start_time: float = 0.0
        self._progress_current: int = 0
        self._progress_total: int = 0
        self._progress_phase: str = ""
        self._refresh_drives()

    def _refresh_drives(self) -> None:
        displays = get_display_strings()
        self._combo.clear()
        self._combo.addItem("Select USB Drive")
        self._combo.addItems(displays)
        if not displays:
            self._status_label.setText("No USB drives found.")

    def _on_convert(self) -> None:
        idx = self._combo.currentIndex()
        if idx <= 0:
            self._status_label.setText("Please select a USB drive.")
            return

        display = self._combo.currentText()
        mountpoint = parse_mountpoint_from_display(display)
        if not mountpoint:
            self._status_label.setText("Invalid drive selection.")
            return

        self._convert_btn.setEnabled(False)
        self._file_list.clear()
        self._file_items.clear()
        self._start_time = time.time()
        self._progress_current = 0
        self._progress_total = 0
        self._progress.setFormat("Elapsed: 0 sec")

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._update_time)
        self._elapsed_timer.start(1000)

        self._worker = ProcessWorker(mountpoint)
        self._worker.status.connect(self._on_status)
        self._worker.progress.connect(self._on_progress)
        self._worker.file_status.connect(self._on_file)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_status(self, msg: str) -> None:
        self._status_label.setText(msg)

    def _on_progress(self, phase: str, current: int, total: int, desc: str) -> None:
        self._progress_phase = phase
        self._progress_current = current
        self._progress_total = max(1, total)
        if phase == "done":
            self._progress.setValue(100)
            self._operation_label.setText("Complete")
        else:
            self._operation_label.setText(f"Processing: {desc}")
            if phase == "analyzing":
                pct = int(50 * current / self._progress_total) if self._progress_total else 0
            else:
                pct = 50 + int(50 * current / self._progress_total) if self._progress_total else 50
            self._progress.setValue(pct)

    def _update_time(self) -> None:
        elapsed = time.time() - self._start_time
        elapsed_str = _format_duration(elapsed)
        if self._progress_total > 0 and self._progress_current > 0:
            remaining = (elapsed / self._progress_current) * (
                self._progress_total - self._progress_current
            )
            text = f"Elapsed: {elapsed_str}  |  ~{_format_duration(remaining)} left"
        else:
            text = f"Elapsed: {elapsed_str}"
        self._progress.setFormat(text)


    def _on_file(self, rel: str, status: str, error_msg: str = "") -> None:
        label = STATUS_LABELS.get(status, status)
        color = STATUS_COLORS.get(status, QColor(255, 255, 255))
        text = f"[{label}] {rel}"
        if status == "failed" and error_msg:
            text += f" — {error_msg}"

        if rel in self._file_items:
            item = self._file_items[rel]
            item.setText(text)
            item.setBackground(color)
            row = self._file_list.row(item)
            if row > 0:
                self._file_list.takeItem(row)
                self._file_list.insertItem(0, item)
        else:
            item = QListWidgetItem(text)
            item.setBackground(color)
            self._file_list.insertItem(0, item)
            self._file_items[rel] = item

    def _on_finished(self) -> None:
        if self._elapsed_timer:
            self._elapsed_timer.stop()
        elapsed = time.time() - self._start_time
        self._progress.setFormat(f"Elapsed: {_format_duration(elapsed)}")
        self._convert_btn.setEnabled(True)


def run_app() -> None:
    app = QApplication([])
    window = PioneerDJCorrectorApp()
    window.show()
    app.exec_()
