import sys

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtWidgets import * # pyright: ignore[reportWildcardImportFromLibrary]


class WarningWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Warning")
        self.setMaximumWidth(500)
        layt = QVBoxLayout()
        self.setLayout(layt)
        self.message = QLabel("Something went wrong :/", self)
        self.message.setWordWrap(True)
        layt.addWidget(self.message)
        
        btn_group = QWidget()
        group_layout = QHBoxLayout()
        btn_group.setLayout(group_layout)

        self.cancel = QPushButton("Cancel")
        self.cancel.pressed.connect(self.close)
        self.retry = QPushButton("Try again")
        self.retry.pressed.connect(self.close)
        group_layout.addWidget(self.cancel)
        group_layout.addWidget(self.retry)
        layt.addWidget(btn_group)


    def warn(self, title, message, retry_call=None):
        self.setWindowTitle(title)
        self.message.setText(message)
        if retry_call is None:
            self.retry.hide()
        else:
            self.retry.pressed.disconnect()
            self.retry.pressed.connect(self.close)
            self.retry.pressed.connect(retry_call)
        self.show()


class DialogWindow(QDialog):
    def __init__(self, title, text):
        super().__init__()

        self.setWindowTitle(title)
        self.layt = QVBoxLayout()
        self.setLayout(self.layt)
        message = QLabel(text)
        self.layt.addWidget(message)

        btns = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(btns)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layt.addWidget(self.buttonBox)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = WarningWindow()
    sys.exit(app.exec())
