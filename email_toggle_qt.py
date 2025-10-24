# email_toggle_qt.py
# A simple PyQt5 window with a single Email ON/OFF button and indicator

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtCore import Qt
import sys

class EmailToggleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Email ON/OFF Control")
        self.setFixedSize(200, 120)
        self.email_on = False

        self.label = QLabel("Email Capability:")
        self.label.setAlignment(Qt.AlignCenter)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.update_status()

        self.button = QPushButton("Email ON / OFF")
        self.button.clicked.connect(self.toggle_email)
        self.button.setMinimumHeight(40)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def update_status(self):
        if self.email_on:
            self.status_label.setText("ON")
            self.status_label.setStyleSheet("background-color: green; color: white; font-weight: bold; font-size: 18px; border-radius: 10px; padding: 6px;")
        else:
            self.status_label.setText("OFF")
            self.status_label.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 18px; border-radius: 10px; padding: 6px;")

    def toggle_email(self):
        self.email_on = not self.email_on
        self.update_status()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EmailToggleWindow()
    win.show()
    sys.exit(app.exec_())
