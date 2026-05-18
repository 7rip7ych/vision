import sys
from time import time
import re
from pathlib import Path

from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QAbstractTableModel, pyqtSignal
# from PyQt6.QtWidgets import QApplication, QFileDialog, QTableView, QMainWindow, QHeaderView, QStatusBar, QLabel, QWidget
from PyQt6.QtWidgets import *
# from click import group
import pandas as pd
import numpy as np
from pandas import isna
import src.file as f
import src.tabs as tab
import src.data as d
import src.filter as flt
import src.warning as w

class TableModel(QAbstractTableModel):

    def __init__(self, data):
        super().__init__()
        self._original_data = data
        self._data = data
        self.headers = data.columns.to_list()
        self.state_col = self.headers.index("State") if "State" in self.headers else False
        self.filter_model = flt.FilterModel()
        self.filter_model.set_data(data)
        self.filter_model.valueUpdated.connect(lambda: self.changeLayout(self.filter_model.get_filtered_data()))
        # print(data.dtypes)

    def get_data(self) -> pd.DataFrame:
        return self._data

    def data(self, index, role):
        value = self._data.iloc[index.row(), index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)

        if len(self.headers) == 2 and index.column() == 0 and role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignRight

        if not self.state_col:
            return

        state = self._data.iat[index.row(), self.state_col]

        if role == Qt.ItemDataRole.BackgroundRole:
            color = 'white'
            match state:
                case 1:
                    color = 'green'
                case 2:
                    color = 'red'
                case 16:
                    color = 'yellow'
            return QtGui.QColor(color)

        if role == Qt.ItemDataRole.ForegroundRole:
            color = 'black'
            match state:
                case 1:
                    color = 'white'
                case 2:
                    color = 'white'
                case 16:
                    color = 'black'
            return QtGui.QColor(color)

    def rowCount(self, index=0):
        if not self._data.empty:
            return self._data.shape[0]
        else:
            return 0

    def count_rows(self):
        if not self._data.empty:
            return (self._original_data.shape[0], self._data.shape[0])
        else:
            return (self._original_data.shape[0], 0)

    def columnCount(self, index=0):
        if not self._data.empty:
            return self._data.shape[1]
        else:
            return 0

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])

    def changeLayout(self, new_data:pd.DataFrame):
        self.layoutAboutToBeChanged.emit()
        self._data = new_data
        self.layoutChanged.emit()

    def sort(self, Ncol, order):
        new_data = self._data.sort_values(self.headers[Ncol], ascending=order == Qt.SortOrder.AscendingOrder)
        self.changeLayout(new_data)

    def filter(self, filters:list):
        """
        filters format = [
            {
                columns: [],
                method: "==" | ">" | "in" | "eq" | "gt"
                value: 54 | "R" | 
            }
        ]
        """
        new_data = self._original_data
        filtered = []
        for filter in filters:
            for col in filter["columns"]:
                if col in self.headers:
                    # shorten ts up
                    dtype = new_data.dtypes[col]
                    val = filter["value"]
                    if dtype == "int64" and filter["method"] in ["eq", "gt", "lt", "ge", "le"]:
                        try:
                            val = int(val)
                        except:
                            continue
                    match filter["method"]:
                        case "eq":
                            if dtype == "datetime64[ns]":
                                # try:
                                #     val = pd.to_datetime(val)
                                # except:
                                #     continue
                                # filtered.append(new_data[new_data[col].dt.strftime(r"%Y-%m-%d %H:%M:%S.%f").startswith(val)])
                                filtered.append(new_data[new_data[col].astype("str").str.startswith(val)])
                            else:
                                filtered.append(new_data[new_data[col] == val])
                        case "gt":
                            filtered.append(new_data[new_data[col] > val])
                        case "lt":
                            filtered.append(new_data[new_data[col] < val])
                        case "in":
                            # if dtype == "object":
                            #     filtered.append(new_data[new_data[col].str.contains(val)])
                            filtered.append(new_data[new_data[col].astype("str").str.contains(val)])
        
        new_data2 = self.join_dataframes(filtered)


        self.changeLayout(new_data2)

    def setFilterString(self, string, case_sensitive=True, match_whole_cell=False, is_regex=False):
        # take "" as exact match
        if not string:
            # make filtered data
            self.changeLayout(self.filter_model.get_filtered_data())
            return

        df = self.filter_model.search(string, case_sensitive, match_whole_cell, is_regex)
        if isinstance(df, pd.DataFrame):
            self.changeLayout(df)

    def join_dataframes(self, tables):
        df = pd.concat(tables, axis=0)
        df = df.sort_values(self.headers[0], ascending=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def export_to_file(self, format, filename, filedir=None):
        match format:
            case "excel" | "exc" | "xlsx":
                if not filedir:
                    path = str(Path.home() / "Downloads" / filename)
                else:
                    path = filedir + "/" + filename
                
                if "." not in filename:
                    path = path + ".xlsx"
                self._data.to_excel(path)
                print(path)
    
    def check_recurring_words(self, column):
        lst = np.asarray(column)
        ext_lst = [item.split() for item in lst]
        counter = {}
        for message in ext_lst:
            for word in message:
                counter[word] = counter.get(word, 0) + 1
        srtd = d.sort_dict_by_val(counter)
        return [item for item in srtd if item[1] > 1]


# for styling maybe
class FormattedTableView(QTableView):
    def __init__(self):
        super().__init__()
        # self.setStyleSheet("""
        #                 QTableView {
        #                     selection-background-color: qlineargradient(x1: 0, y1: 0, x2: 0.5, y2: 0.5,
        #                                                 stop: 0 #FF92BB, stop: 1 white);
        #                     selection-color: black;
        #                 }

        #                 QTableView::item
        #                 {
        #                     border: inherit;
        #                     padding: 2px;
        #                 }
        #                 """)

    def sizeHintForColumn(self, column):
        return super().sizeHintForColumn(column) #+ 5



class TableWindow(QMainWindow):
    dataUpdated = pyqtSignal(pd.DataFrame)
    infoUpdated = pyqtSignal(pd.DataFrame)
    def __init__(self):
        super().__init__()
        self.df = None
        self.file_paths = []
        self.info_window = False
        # self.filter_model = flt.FilterModel()
        self.init_headers = ["Counter", "DateTime", "TimeDiff", "MsgNr", "Class", "Classname", "Type", "State", "StateText", "Text1", "Zone_beta", "Zone", "Group"]
        self.shown_headers = ["Counter", "DateTime", "TimeDiff", "MsgNr", "Class", "Classname", "Type", "State", "StateText", "Text1", "Zone_beta", "Zone", "Group"]
        self.columnWidths = {
                                "Counter": 121,
                                "DateTime": 149,
                                "TimeDiff": 58,
                                "MsgNr": 67,
                                "Class":39,
                                "Classname": 70,
                                "Type": 39,
                                "State": 39,
                                "StateText": 63,
                                "Text1": 1010,
                                "Zone_beta": 39,
                                "Zone": 60,
                                "Group": 60
                            }
        self.filter_window = flt.FilterWindow(self.shown_headers)
        self.export_window = ExportWindow()
        self.setWindowTitle("Table view")
        self.setGeometry(100, 100, 1200, 600)
        self.create_menu()
        self.create_status_bar()
        self.warnings = w.WarningWindow()
        self.alarm_list = None
        self.is_empty = True
        self.config_files = f.load_config()
        self.zone_dict = {}
        self.make_zone_dict()

    def closeEvent(self, a0):
        self.hide()
        a0.ignore()

    def get_data(self):
        return self.df

    def make_zone_dict(self):
        if not self.config_files: return
        self.zone_dict = {}
        zones = self.config_files[0]["Zone"].to_list()
        for zone in zones:
            key = re.search(r"\d{2}[a-zA-Z]{1}", zone)
            if not key or not key.group(): continue
            self.zone_dict[key.group()] = zone

    def print_info(self, opt):
        if self.df is None: return
        if not self.info_window or not isinstance(self.info_window, tab.MainWindow):
            self.info_window = tab.MainWindow()
        # print(opt)
        # add tab
        page = QWidget(self.info_window)
        title = "Info"
        match opt:
            case "overview":
                title = "General"
                layout = QVBoxLayout()
                page.setLayout(layout)
                data = d.get_info(self.df)

                wdgt = QLabel(data)
                layout.addWidget(wdgt)

            case "memory":
                title = "Memory"
                layout = QVBoxLayout()
                page.setLayout(layout)
                data = d.get_mem_info(self.df)

                tbl = QTableView()
                model = TableModel(data)
                tbl.setModel(model)
                tbl.setSortingEnabled(True)
                layout.addWidget(tbl)

            case "unique":
                title = "Unique"
                layout = QHBoxLayout()
                page.setLayout(layout)
                tabs = QTabWidget(page)
                layout.addWidget(tabs)
                tabs.setMovable(True)
                dfs = d.get_unique_values(self.df, ["Counter", "DateTime", "Ms"])
                for col, df in dfs.items():
                    tbl = QTableView()
                    model = TableModel(df)
                    tbl.setModel(model)
                    tbl.setSortingEnabled(True)
                    tabs.addTab(tbl, col)

            case "files":
                title = "Files"
                layout = QVBoxLayout()
                page.setLayout(layout)
                for path in self.file_paths:
                    layout.addWidget(QLabel(path))
                # print(self.file_paths)
            
            case "alarms":
                if self.alarm_list is None: return
                title = "Alarms"
                layout = QVBoxLayout()
                page.setLayout(layout)
                # data = d.get_mem_info(self.df)

                tbl = QTableView()
                model = TableModel(self.alarm_list)
                tbl.setModel(model)
                tbl.setSortingEnabled(True)
                tbl.sortByColumn(0, Qt.SortOrder.AscendingOrder)
                layout.addWidget(tbl)
                # recur = self.model.check_recurring_words(self.alarm_list["Text1"])
                # print(recur[:50])

        self.info_window.new_tab(title, page)
        self.info_window.show()

    def create_menu(self):
        self.menu = self.menuBar()
        if not isinstance(self.menu, QMenuBar): return
        self.menu_options = {
            "file": self.menu.addMenu('&File'),
            "info": self.menu.addMenu('&Info'),
            "columns": self.menu.addMenu('&Columns'),
            "filter": self.menu.addMenu('&Filter'),
            "analyze": self.menu.addMenu('&Analyze')
        }
        if isinstance(self.menu_options['file'], QMenu):
            self.menu_options['file'].addAction('Open', lambda: self.open_files())
            self.menu_options['file'].addAction('Import', lambda: self.add_files())
            self.menu_options['file'].addAction('Export', lambda: self.export())
            self.menu_options['file'].addAction('Exit', self.destroy)

        if isinstance(self.menu_options['info'], QMenu):
            self.menu_options['info'].addAction('Overview', lambda: self.print_info("overview"))
            self.menu_options['info'].addAction('Current file', lambda: self.print_info("files"))
            self.menu_options['info'].addAction('Unique', lambda: self.print_info("unique"))
            self.menu_options['info'].addAction('Memory', lambda: self.print_info("memory"))
            self.menu_options['info'].addAction('Alarm list', lambda: self.print_info("alarms"))

        if isinstance(self.menu_options['filter'], QMenu):
            self.menu_options['filter'].addAction('Add filter', lambda: self.filter_window.view("add"))
            self.menu_options['filter'].addAction('View filters', lambda: self.filter_window.view("view"))
            self.menu_options['filter'].addAction('Edit filters', lambda: self.filter_window.view("edit"))
            self.menu_options['filter'].addAction('Clear filters', self.filter_window.clear)

        # self.menu_options['analyze'].addAction('Open')
        # self.menu_options['analyze'].addAction('Update')

    def create_status_bar(self):
        """ Bottom bar """
        self.status_bar = self.statusBar()
        self.perma_label = QLabel("Vision Viewer v1.0")
        self.status_bar.addWidget(self.perma_label)

        self.row_count = QLabel("Rows: 00")
        self.status_bar.addPermanentWidget(self.row_count)

    def count_rows(self):
        rows = self.model.count_rows()
        self.row_count.setText(f"{rows[1]} / {rows[0]} rows")

    def open_files(self, mode="default", query="view"):
        """ Open files """
        try:
            tm0 = time()
            self.query = query
            tables = self.load_data(True, mode)
            tm1 = time()
            if not tables:
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            self.df = self.join_dataframes(tables)
            tm2 = time()
            self.create_view_based_on_model()
            self.dataUpdated.emit(self.df)
            QApplication.restoreOverrideCursor()
            tm3 = time()
            print("-----open files-----")
            print(f"load data: {tm1-tm0:.4f}")
            print(f"join: {tm2-tm1:.4f}")
            print(f"create view: {tm3-tm2:.4f}")
            print("------------------")
        except Exception as e:
            call_function = self.open_files
            self.warnings.warn("Something went wrong", repr(e), call_function)
            print(e)
            return


    def add_files(self):
        """ Add more data files """
        tables = self.load_data(False)
        if not tables:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.df = self.join_dataframes([self.df, *tables])
        self.create_view_based_on_model()
        self.dataUpdated.emit(self.df)
        QApplication.restoreOverrideCursor()

    def load_data(self, override:bool=True, mode="default"):
        tm0 = time()
        if mode == "debug":
            paths = [r"C:\Users\idaho\Documents\Scania\AlarmLogging\DESKTOP-HFS4KSQ_HMI#33IR_ALG_202502172300_202502182300.mdf"]
        else:
            file_paths, _ = QFileDialog.getOpenFileNames(
                None,
                "Select files",
                r"E:\Savelli_larmanalys\20251104_Z39A_Main\HMI_33IR\ArchiveManager\AlarmLogging",
                "Database files (*.mdf);;All Files (*)"
            )
            if not file_paths:
                return
            # print("Selected files: ", file_paths)
            # eliminate dupes
            paths = [path for path in file_paths if path not in self.file_paths] if self.file_paths else file_paths

        if not paths:
            return

        if override:
            self.file_paths = paths
        else:
            self.file_paths = self.file_paths + paths
        tm1 = time()
        try:
            if self.alarm_list is None:
                tables, self.alarm_list = f.load_files(paths, self.query, True)
                self.infoUpdated.emit(self.alarm_list)
            else:
                tables = f.load_files(paths, self.query, False)
        except Exception as e:
            call_function = self.open_files if override else self.add_files
            self.warnings.warn("File error", ("Could not access file. \nCheck that SQL Express works correctly and has the necessary permissions to read the file. \n" + repr(e)), call_function)
            print(e)
            return
        tm2 = time()
        # for table in tables:
        #     table = self.format_data(table)
        #     print(table.columns)
        formatted = [self.format_data(table) for table in tables]
        tm3 = time()
        print("-----load data-----")
        print(f"path: {tm1-tm0:.4f}")
        print(f"load: {tm2-tm1:.4f}")
        print(f"format: {tm3-tm2:.4f}")
        print("------------------")
        return formatted

    def join_dataframes(self, tables):
        df = pd.concat(tables, axis=0)
        df.reset_index(drop=True, inplace=True)
        return df

    def format_data(self, df:pd.DataFrame):
        # merge datetime and ms
        df["DateTime"] = (df["DateTime"] + pd.to_timedelta(df["Ms"], 'milliseconds'))
        df.drop("Ms", axis=1, inplace=True)
        # get zones
        cal_zones = df["Text1"].str.extract(r"\D(\d{2}[a-zA-Z]{1})\D")
        df.insert(loc=10, column = 'Zone_beta', value = cal_zones)

        # get groups
        if self.config_files:
            tm0 = time()
            alist = self.config_files[0] # zones
            if "ID" in alist.columns: alist.rename(columns={"ID": "MsgNr"}, inplace=True)

            zn_grp = self.config_files[1][["Zone", "Group"]] # groups
            # alist = alist.merge(zn_grp, how='left', on='Zone')
            df = df.merge(alist[["MsgNr", "Zone"]], how='left', on='MsgNr')
            comb = df["Zone"].combine_first(df["Zone_beta"])
            tm1 = time()
            df["Zone"] = comb.str.replace(r"^\d{2}[a-zA-Z]{1}$", repl=self.get_zone_name, regex=True)

            df = df.merge(zn_grp[["Zone", "Group"]], how='left', on='Zone')

            tm2 = time()
            # print("-----format data-----")
            # print(f"pt1: {tm1-tm0:.4f}")
            # print(f"pt2: {tm2-tm1:.4f}")
        df.replace("<No value>", "")
        df.fillna("", inplace=True)
        tm3 = time()
        # print(f"replace: {tm3-tm2:.4f}")
        # print("------------------")
        return df

    def get_zone_name(self, match):
        nr = match.string
        return self.zone_dict[nr] if nr in self.zone_dict else nr
    
    def create_view_based_on_model(self):
        self.table_view = FormattedTableView()

        tm0 = time()
        self.model = TableModel(self.df)
        self.table_view.setModel(self.model)
        self.filter_window.set_model(self.model.filter_model)
        self.model.layoutChanged.connect(self.count_rows)
        self.model.layoutChanged.connect(self.check_empty)
        self.model.layoutChanged.connect(lambda: self.dataUpdated.emit(self.model.get_data()))
        self.is_empty = False
        tm1 = time()
        self.table_view.setSortingEnabled(True)
        tm2 = time()
        # self.table_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.model.sort(0, Qt.SortOrder.AscendingOrder)
        tm3 = time()

        # search
        widg = QWidget()
        layt = QHBoxLayout()
        widg.setLayout(layt)

        
        layt.setContentsMargins(0, 5, 0, 5)
        layt.setSpacing(3)

        min_size = QSizePolicy()
        min_size.setHorizontalPolicy(QSizePolicy.Policy.Fixed)
        min_size.setVerticalStretch(1)
        min_size.setHorizontalStretch(0)

        case_sense = QPushButton("Aa")
        case_sense.setCheckable(True)
        case_sense.setToolTip("Case sensitive")
        case_sense.setSizePolicy(min_size)
        case_sense.setFixedWidth(30)
        layt.addWidget(case_sense)

        match_whole = QPushButton("a͟b͟c͟")
        match_whole.setCheckable(True)
        match_whole.setToolTip("Match whole cell")
        match_whole.setSizePolicy(min_size)
        # match_whole.setStyleSheet("""QPushButton {  }""")
        match_whole.setFixedWidth(40)
        layt.addWidget(match_whole)

        reg_enabled = QPushButton(".*")
        reg_enabled.setCheckable(True)
        reg_enabled.setToolTip("Use regular expression")
        reg_enabled.setSizePolicy(min_size)
        reg_enabled.setFixedWidth(30)
        layt.addWidget(reg_enabled)

        searchbar = QLineEdit()
        searchbar.setPlaceholderText('ex. Counter="5", "U", r')
        searchbar.setClearButtonEnabled(True)
        layt.addWidget(searchbar)

        enter_button = QPushButton("Search")
        layt.addWidget(enter_button)

        change_action = lambda: self.model.setFilterString(searchbar.text(), case_sense.isChecked(), match_whole.isChecked(), reg_enabled.isChecked())
        
        # searchbar.textChanged.connect(change_action)
        searchbar.returnPressed.connect(change_action)
        enter_button.pressed.connect(change_action)
        # case_sense.toggled.connect(change_action)
        # match_whole.toggled.connect(change_action)
        # reg_enabled.toggled.connect(change_action)
        self.searchbar = [searchbar, case_sense, match_whole, reg_enabled, enter_button]
        

        self.resizeColumns()
        tm4 = time()
        self.menu_options["columns"].clear()
        self.column_checks = []
        for col in self.model.headers:
            if col not in self.shown_headers and col in self.model.headers:
                self.table_view.hideColumn(self.model.headers.index(col))
            act = self.create_check_action(col, col in self.shown_headers)
            self.column_checks.append(act)
            self.menu_options['columns'].addAction(act)

        # self.row_count.setText(f"Rows: {self.model.rowCount()}")
        self.count_rows()
        
        lay = QVBoxLayout()
        lay.addWidget(widg)
        lay.addWidget(self.table_view)

        self.table_cont = QWidget()
        self.table_cont.setLayout(lay)

        self.setCentralWidget(self.table_cont)


        print("---create view---")
        print(f"model: {tm1-tm0:.4f}")
        print(f"sort enable: {tm2-tm1:.4f}")
        print(f"sort: {tm3-tm2:.4f}")
        print(f"search & resize: {tm4-tm3:.4f}")
        print("--------")

        self.show()

    def resizeColumns(self):

        """ Sets width to fit content for main columns. """
        # tm0 = time()
        # self.table_view.resizeColumnsToContents() # slow
        # tm1 = time()

        for col in self.shown_headers:
            if all(col in lst for lst in [self.model.headers, self.columnWidths.keys()]):
                wid = self.columnWidths[col]

                i = self.model.headers.index(col)
                self.table_view.setColumnWidth(i, wid)
        # tm2 = time()
        # print("---Resize columns---")
        # print(f"Built-in auto resize: {tm1-tm0:.7f}")
        # print(f"With set values: {tm2-tm1:.7f}")
        # print("--------")
        self.show()

    def check_empty(self):
        """ Sets column widths when going from empty table. """
        new_state = self.model.get_data().empty
        old_state = self.is_empty
        if new_state == old_state:
            return
        if not new_state:
            self.resizeColumns()
        self.is_empty = new_state


    def create_check_action(self, name, checked=False):
        check_action = QtGui.QAction(name, self)
        check_action.setStatusTip("Toggle column visibility")
        check_action.triggered.connect(lambda: self.toggle_column(check_action.text()))
        check_action.setCheckable(True)
        check_action.setChecked(checked)
        return check_action

    def toggle_column(self, column):
        self.menu_options['columns'].show()
        i = self.model.headers.index(column)
        if self.table_view.isColumnHidden(i):
            self.table_view.showColumn(i)
            if column not in self.shown_headers: self.shown_headers.append(column)
        else:
            self.table_view.hideColumn(i)
            if column in self.shown_headers: self.shown_headers.remove(column)

    def export(self):
        self.export_window.set_data(self.model.get_data())
        self.export_window.show()

        # self.model.export_to_file("excel", "test")
        # print("not yet")

class ExportWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Export settings")
        layt = QVBoxLayout()
        self.setLayout(layt)
        self.lay = layt

        self.name_field = QLineEdit(self)
        layt.addWidget(QLabel("Enter a filename:"))
        layt.addWidget(self.name_field)

        radio_btns = QWidget()
        radio_layt = QHBoxLayout(radio_btns)
        radio_btns.setLayout(radio_layt)
        self.radio1 = QRadioButton("Excel (.xlsx)")
        self.radio1.setChecked(True)
        # self.radio1.toggled.connect(lambda: self.execute("xlsx"))
        radio_layt.addWidget(self.radio1)

        self.radio2 = QRadioButton("CSV (.csv)")
        radio_layt.addWidget(self.radio2)

        layt.addWidget(radio_btns)

        self.submit_button = QPushButton("Save")
        self.submit_button.pressed.connect(self.execute)
        layt.addWidget(self.submit_button)

    def set_data(self, data):
        self._data = data

    def get_selected_type(self):
        if self.radio1.isChecked():
            return "excel"
        if self.radio2.isChecked():
            return "csv"

    def execute(self):
        name = self.name_field.text()
        file_type = self.get_selected_type()
        self.export_to_file(file_type, name)

    def export_to_file(self, format, filename, filedir=None):
        if not filedir:
            path = str(Path.home() / "Downloads" / filename)
        else:
            path = filedir + "/" + filename
        match format:
            case "excel" | "exc" | "xlsx":
                if "." not in filename:
                    path = path + ".xlsx"
                elif ".csv" not in filename:
                    path = re.sub(r"\..*$", ".xlsx", path)
                self._data.to_excel(path)
            case "CSV" | "csv":
                if "." not in filename:
                    path = path + ".csv"
                elif ".csv" not in filename:
                    path = re.sub(r"\..*$", ".csv", path)
                self._data.to_csv(path)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TableWindow()
    window.open_files()
    window.show()
    app.exec()
