import sys
from time import sleep
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QSplashScreen

class SplashScreen(QSplashScreen):
    def __init__(self):
        super(QSplashScreen, self).__init__()
        self.setWindowFlag(Qt.WindowType.SplashScreen)
        pixmap = QPixmap("UI/images/logo/logo.ico")
        self.setPixmap(pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    sleep(5)
    splash.close()
    sys.exit(app.exec())