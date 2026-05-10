import sys
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QTabWidget
from PyQt6.QtCore import Qt


class MainWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Info window')
        self.setMinimumHeight(300)
        self.setMinimumWidth(300)

        main_layout = QGridLayout(self)
        self.setLayout(main_layout)

        # create a tab widget
        self.tab = QTabWidget(self)
        self.tab.setMovable(True)
        self.tab.setTabsClosable(True)
        self.tab.tabCloseRequested.connect(self.close_tab)


        main_layout.addWidget(self.tab, 0, 0, 2, 1)

        # self.show()

    def closeEvent(self, a0):
        self.tab.clear()
        # self.close()
        # a0.ignore()

    def new_tab(self, title, tab_widget):
        for i in range(self.tab.count()):
            if self.tab.tabText(i) == title:
                self.tab.removeTab(i)
        new_i = self.tab.addTab(tab_widget, title)
        self.tab.setCurrentIndex(new_i)
        self.activateWindow()
    
    def close_tab(self, current_index:int):
        curr_widg = self.tab.widget(current_index)
        if curr_widg is not None:
            curr_widg.deleteLater()
            self.tab.removeTab(current_index)
        if self.tab.count() == 0:
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())