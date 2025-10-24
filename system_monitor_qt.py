# system_monitor_qt.py
# PyQt5 version of the system monitor, matching the layout and logic of the original Tkinter version

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGridLayout
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt, QTimer
import subprocess
import time
import os
import sys

PROCESS_LABELS = [
    "Excel Host Ready",
    "Virtual Environment Started",
    "Dashboard Running",
    "Scanner Running",
    "Testing",
    "Test Result Recorded",
    "Dashboard Updated",
    "Building Email",
    "Email ON/OFF",
    "Email Sent"
]

class StatusDot(QLabel):
    def __init__(self, color="#cccccc"):
        super().__init__()
        self.setFixedSize(20, 20)
        self.setStyleSheet(f"background-color: {color}; border-radius: 10px; border: 1px solid #888;")
        self.color = color
    def set_color(self, color):
        self.setStyleSheet(f"background-color: {color}; border-radius: 10px; border: 1px solid #888;")
        self.color = color

class SystemMonitorQt(QWidget):

    def __init__(self):
        super().__init__()
        self.email_on = True  # Default to ON
        self.setWindowTitle("System Monitor")
        self.setFixedSize(320, 420)
        self.status = [False] * len(PROCESS_LABELS)
        self.processes = []
        self.startup_step = 0
        self.startup_time = time.time()
        self.dots = []
        self.labels = []
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh)
        self.timer.start(2000)

    def init_ui(self):
        layout = QVBoxLayout()
        grid = QGridLayout()
        font_size = int(10 * 1.2)  # 20% larger than 10pt
        for i, label_text in enumerate(PROCESS_LABELS):
            if label_text == "Email ON/OFF":
                btn = QPushButton(label_text)
                btn.setStyleSheet(f"font: bold {font_size}pt Arial; color: #000042; background: transparent; border: none; box-shadow: none; padding: 2px; text-align: center;")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.clicked.connect(self.toggle_email)
                btn.setFlat(False)
                btn.setMinimumHeight(28)
                btn.setMinimumWidth(120)
                btn.setMaximumWidth(200)
                btn.setSizePolicy(btn.sizePolicy().Expanding, btn.sizePolicy().Expanding)
                btn.setContentsMargins(0,0,0,0)
                lab = btn
                dot = StatusDot("green")
                self.email_btn = btn
                self.email_dot_idx = i
            else:
                lab = QLabel(label_text)
                lab.setStyleSheet(f"font: bold {font_size}pt Arial; color: #000042; background: transparent; border: none; box-shadow: none; padding: 2px;")
                lab.setAlignment(Qt.AlignCenter)
                dot = StatusDot()
            grid.addWidget(lab, i, 0, alignment=Qt.AlignCenter)
            grid.addWidget(dot, i, 1, alignment=Qt.AlignCenter)
            self.labels.append(lab)
            self.dots.append(dot)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        self.setLayout(layout)

    def toggle_email(self):
        self.email_on = not self.email_on
        color = "green" if self.email_on else "red"
        self.dots[self.email_dot_idx].set_color(color)

    def mark_complete(self, index):
        if 0 <= index < len(self.dots):
            self.dots[index].set_color("green")
            self.status[index] = True

    def _refresh(self):
        current_time = time.time()
        elapsed = current_time - self.startup_time
        # Check for test completion flag
        if os.path.exists('/home/kw/cyl_a/test_complete.flag'):
            if not self.status[5]:  # Test Result Recorded not yet marked
                self.mark_complete(5)
                os.remove('/home/kw/cyl_a/test_complete.flag')
        # Startup sequence with delays
        if self.startup_step == 0 and elapsed > 2:  # Excel Host Ready
            self.mark_complete(0)
            self.startup_step = 1
        elif self.startup_step == 1 and elapsed > 4:  # Virtual Environment Started
            self.mark_complete(1)
            self.startup_step = 2
        elif self.startup_step == 2 and elapsed > 6:  # Dashboard Running
            try:
                p = subprocess.Popen(['./venv/bin/python', 'autoproto.py'], cwd='/home/kw/cyl_a')
                self.processes.append(p)
                self.mark_complete(2)
            except:
                pass
            self.startup_step = 3
        elif self.startup_step == 3 and elapsed > 8:  # Scanner Ready
            try:
                p = subprocess.Popen(['./venv/bin/python', 'scanner_gui.py'], cwd='/home/kw/cyl_a')
                self.processes.append(p)
                self.mark_complete(3)
            except:
                pass
            self.startup_step = 4
        elif self.startup_step == 4 and elapsed > 10:  # Testing - removed auto trigger
            # Testing only activates when barcode is scanned
            self.startup_step = 5

    def toggle_email(self):
        self.email_on = not self.email_on
        color = "green" if self.email_on else "red"
        self.dots[self.email_dot_idx].set_color(color)

    def mark_complete(self, index):
        if 0 <= index < len(self.dots):
            self.dots[index].set_color("green")
            self.status[index] = True

    def _refresh(self):
        current_time = time.time()
        elapsed = current_time - self.startup_time
        # Check for test completion flag
        if os.path.exists('/home/kw/cyl_a/test_complete.flag'):
            if not self.status[5]:  # Test Result Recorded not yet marked
                self.mark_complete(5)
                os.remove('/home/kw/cyl_a/test_complete.flag')
        # Startup sequence with delays
        if self.startup_step == 0 and elapsed > 2:  # Excel Host Ready
            self.mark_complete(0)
            self.startup_step = 1
        elif self.startup_step == 1 and elapsed > 4:  # Virtual Environment Started
            self.mark_complete(1)
            self.startup_step = 2
        elif self.startup_step == 2 and elapsed > 6:  # Dashboard Running
            try:
                p = subprocess.Popen(['./venv/bin/python', 'autoproto.py'], cwd='/home/kw/cyl_a')
                self.processes.append(p)
                self.mark_complete(2)
            except:
                pass
            self.startup_step = 3
        elif self.startup_step == 3 and elapsed > 8:  # Scanner Ready
            try:
                p = subprocess.Popen(['./venv/bin/python', 'scanner_gui.py'], cwd='/home/kw/cyl_a')
                self.processes.append(p)
                self.mark_complete(3)
            except:
                pass
            self.startup_step = 4
        elif self.startup_step == 4 and elapsed > 10:  # Testing - removed auto trigger
            # Testing only activates when barcode is scanned
            self.startup_step = 5

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SystemMonitorQt()
    win.show()
    sys.exit(app.exec_())
