"""
Test application
"""
# ~\ python -m PyInstaller main.spec
import sys
import os
from time import strftime, localtime, sleep, time
from os import path

from PyQt6.QtGui import QIcon, QFontDatabase
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, pyqtSlot, QAbstractTableModel, Qt, QModelIndex, QUrl, QSortFilterProxyModel
from PyQt6.QtWidgets import QApplication, QFileDialog, QTableView, QWidget, QMainWindow, QHeaderView, QMenu
from PyQt6.QtQuick import QQuickView, QQuickItem, QQuickWindow
import pandas as pd
import src.file as f
import src.data as d
import src.table as t
import src.analyze as a
import src.splash as s


# paths
bundle_dir = path.abspath(path.dirname(__file__))
qml_path = path.join(bundle_dir, 'UI/main.qml')

total1 = time()
# start app
app = QApplication(sys.argv)
app.setWindowIcon(QIcon(os.path.join(bundle_dir, 'UI/images/logo/draft1.2_vision_logo_thicker (3).ico')))

splash = s.SplashScreen()
splash.show()

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.quit.connect(app.closeAllWindows)
engine.quit.connect(sys.exit)

if not os.path.exists(qml_path):
    raise FileNotFoundError(qml_path)
engine.load(qml_path)

window = engine.rootObjects()[0]

# class MainWindow(QMainWindow):

#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Main")


tm0 = time()
main = t.TableWindow()
# main.load_data()
tm1 = time()
an = a.AnalysisWindow(filter_window=main.filter_window)
tm2 = time()
main.dataUpdated.connect(an.table_changed)
main.infoUpdated.connect(an.load_info)


def connect_windows(iteration=0):
    if not main.menu_options:
        sleep(0.0001)
        return connect_windows(iteration+1) if iteration < 5 else None
    if isinstance(main.menu_options['analyze'], QMenu):
        main.menu_options['analyze'].addAction('Open', lambda: an.open_and_load(main.df))
        main.menu_options['analyze'].addAction('Update', lambda: an.load_data(main.df))

connect_windows()

tm3 = time()
print(f"create table: {tm1-tm0:.4f}")
print(f"create analysis: {tm2-tm1:.4f}")
print(f"connections: {tm3-tm2:.4f}")
# signals
class Backend(QObject):

    updated_time = pyqtSignal(str, arguments=['time'])
    # updated_background = pyqtSignal(str, arguments=['path'])

    def __init__(self):
        super().__init__()

        # Define timer.
        self.timer = QTimer()
        self.timer.setInterval(100)  # msecs 100 = 1/10th sec
        self.timer.timeout.connect(self.update_time)
        self.timer.start()

    def update_time(self):
        # Pass the current time to QML.
        curr_time = strftime("%H:%M:%S", localtime())
        self.updated_time.emit(curr_time)

    @pyqtSlot()
    def input_files(self):
        main.open_files(query="view")

    @pyqtSlot()
    def input_files_all(self):
        main.open_files(query="all")

    @pyqtSlot()
    def skip(self):
        main.open_files("debug")
    
    @pyqtSlot()
    def open_analyzer(self):
        if main.df is None:
            main.open_files(query="view")
        else:
            an.open_and_load(main.df)


    @pyqtSlot()
    def off(self):
        main.close()
        an.close()
        app.quit()



backend = Backend()
window.setProperty('backend', backend)

if 'debug' in sys.argv:
    print("loading...")
    tm4 = time()
    main.open_files("debug")
    tm5 = time()
    if main.df is not None and not main.df.empty:
        an.open_and_load(main.df)
    tm6 = time()
    print(f"open table: {tm5-tm4:.4f}")
    print(f"open analysis: {tm6-tm5:.4f}")
total2 = time()
print("total", total2-total1)
splash.finish(main)
sys.exit(app.exec())

