import sys
# from PyQt6.QtWidgets import QApplication, QWidget,  QFormLayout, QGridLayout, QTabWidget, QLineEdit, QDateEdit, QPushButton, QButtonGroup, QHBoxLayout, QMainWindow, QStackedLayout, QVBoxLayout
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QObject
import pandas as pd
import re
import datetime as dt
from collections import Counter

class FilterModel(QObject):
    valueUpdated = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.lst = []
        self.dependency = "dependent"
        self._original_data = pd.DataFrame()
        self._filtered_data = pd.DataFrame()

    def get(self):
        return self.lst

    def __str__(self):
        return str(*self.lst)

    def __add__(self, filter):
        self.add(filter)
    
    def set_data(self, df:pd.DataFrame):
        self._original_data = df
        self._filtered_data = df
    
    def get_filtered_data(self) -> pd.DataFrame:
        return self._filtered_data

    def set_filters(self, filters:list):
        self.lst = filters
        self._filtered_data = self.apply(self._original_data, filters, self.dependency)
        self.valueUpdated.emit()

    def add(self, filter:dict):
        """ """
        if not filter["columns"] or not filter["method"] or not filter["value"]: return
        if filter in self.lst: return
        self.lst.append(filter)
        
        if self.dependency == "dependent" or len(self.lst) == 1:
            self._filtered_data = self.apply(self._filtered_data, [filter], self.dependency)
        elif self.dependency == "independent":
            res = self.apply(self._original_data, [filter], self.dependency)
            self._filtered_data = self.join_dataframes([self._filtered_data, res])
        else:
            self._filtered_data = self.apply(self._original_data, self.lst, self.dependency)

        self.valueUpdated.emit()

    def remove(self, filter):
        """ """
        self.lst.remove(filter)
        self._filtered_data = self.apply(self._original_data, self.lst, self.dependency)
        self.valueUpdated.emit()

    def clear(self):
        """ """
        print("clear")
        self.lst = []
        self._filtered_data = self._original_data
        self.valueUpdated.emit()

    def apply(self, df:pd.DataFrame, filters:list, mode:str="") -> pd.DataFrame:
        """
        modes: dependent, independent
        filters format = [
            {
                columns: [],
                method: "==" | ">" | "in" | "eq" | "gt"
                value: 54 | "R"| [1,2],
                case_sensitive: bool,
                is_regex: bool
            }
        ]
        """
        if not filters:
            return df

        if not mode:
            mode = self.dependency
        columns = df.columns.to_list()
        if mode == "dependent":
            dep_df = df
        elif mode == "independent_columns":
            flts = self.sort_filters_by_column(filters)
            return self.filter_column_independent(flts[0], flts[1], df)

        filtered = []
        for filter in filters:
            for col in filter["columns"]:
                if col in columns:
                    cas = filter.get("case_sensitive", True)
                    reg = filter.get("is_regex", False)
                    try:
                        if mode == "dependent":
                            res = self.filter_column(dep_df, col, filter["method"], filter["value"], cas, reg)
                        else:
                            res = self.filter_column(df, col, filter["method"], filter["value"], cas, reg)
                    except re.PatternError:
                        return pd.DataFrame()
                    if isinstance(res, pd.DataFrame): filtered.append(res)

            if mode == "dependent":
                # column independent, filter dependent
                dep_df = self.join_dataframes(filtered)
                filtered = []
        if mode == "dependent":
            return dep_df

        if len(filtered) >= 2:
            return self.join_dataframes(filtered)
        elif len(filtered) == 1:
            return filtered[0]
        else:
            return pd.DataFrame()

    def filter_column(self, df:pd.DataFrame, column, method, value, case_sen=True, is_reg=False):
        """ """
        # shorten ts up
        res = None
        dtype = df.dtypes[column]
        if not value or not column or not method or df.empty: return
        if method not in ["sub", "in", "rng"] and not is_reg:
            try:
                if dtype == "int64":
                    value = int(value)
                elif dtype == "datetime64[ns]" and method not in ["eq", "=", "==", "equal"]:
                    value = pd.to_datetime(value)

            except ValueError:
                return

        match method:
            case "eq" | "=" | "==" | "equal":
                if is_reg:
                    res = df[df[column].astype("str").str.fullmatch(value, case_sen)]
                elif dtype == "datetime64[ns]" and isinstance(value, str) and len(value) >= 4:
                    res = df[df[column].astype("str").str.startswith(value)]
                elif not case_sen and isinstance(value, str):
                    res = df[df[column].astype("str").str.lower() == value.lower()]
                else:
                    res = df[df[column] == value]
            case "not" | "!=":
                if is_reg:
                    res = df[not df[column].astype("str").str.fullmatch(value, case_sen)]
                elif dtype == "datetime64[ns]" and isinstance(value, str) and len(value) >= 4:
                    res = df[not df[column].astype("str").str.startswith(value)]
                elif not case_sen and isinstance(value, str):
                    res = df[df[column].astype("str").str.lower() != value.lower()]
                else:
                    res = df[df[column] != value]
            case "sub":
                if not isinstance(value, str): return
                # if is_reg:
                #     res = df[df[column].astype("str").str.match(".*" + value, case_sen)]
                if case_sen:
                    res = df[df[column].astype("str").str.contains(value, regex=is_reg)]
                else:
                    res = df[df[column].astype("str").str.lower().str.contains(value.lower(), regex=is_reg)]
            case "in":
                if not (isinstance(value, tuple) or isinstance(value, list)): return
                if dtype == "datetime64[ns]":
                    for item in value:
                        matches = df[df[column].astype("str").str.startswith(item)]
                        if not matches.empty: res = matches
                else:
                    res = df[df[column].astype("str").isin(value)]

            case "rng" | "range":
                if not (isinstance(value, tuple) or isinstance(value, list)): return
                try:
                    # Format if int or datetime
                    if dtype == "datetime64[ns]":
                        low_bound = pd.to_datetime(value[0])
                        high_bound = pd.to_datetime(value[1])
                    elif dtype == "int64":
                        low_bound = int(value[0])
                        high_bound = int(value[1])
                    else:
                        print("not possible")
                        return
                except:
                    print("failed")
                    return
                fdf = df[df[column] >= low_bound]
                fdf = fdf[fdf[column] <= high_bound]
                res = fdf
            case "gt" | ">":
                res = df[df[column] > value]
            case "lt" | "<":
                res = df[df[column] < value]
            case "ge" | ">=":
                res = df[df[column] >= value]
            case "le" | "<=":
                res = df[df[column] <= value]
        return res

    def sort_filters_by_column(self, filters:list) -> tuple:
        """ """
        cols = []
        unique_filters = []
        column_filters = {}
        for obj in filters:
            cols.extend(obj["columns"])
        
        print(cols)
        counts = Counter(cols)
        dupes = list(set(col for col in cols if counts[col] > 1))
        for d in dupes:
            column_filters[d] = []
        print(dupes)
        for obj in filters:
            for col in dupes:
                if col not in obj["columns"]:
                    continue

                column_filters[col].append({
                    "columns": [col],
                    "method": obj["method"],
                    "value": obj["value"]
                })
            
            # obj["columns"].remove(col)

            if len(obj["columns"]) < 1:
                continue
            unique_columns = [x for x in obj["columns"] if x not in dupes]
            if len(unique_columns) >= 1:
                unique_filters.append({
                    "columns": unique_columns,
                    "method": obj["method"],
                    "value": obj["value"]
                })
        print(column_filters)
        print(unique_filters)
        return (unique_filters, column_filters.values())
    
    def filter_column_independent(self, dependent_filters:list, independent_filters:list, data):
        """ """
        df = self.apply(data, dependent_filters, "dependent")
        for filt in independent_filters:
            df = self.apply(df, filt, "independent")
        return df



    def search(self, string, case_sensitive=True, match_whole_cell=False, is_regex=False):
        # take "" as exact match

        df = self._filtered_data
        filters = [{
            "columns": [],
            "method": None,
            "value": None,
            "case_sensitive": case_sensitive,
            "is_regex": is_regex
        }]

        spl = string.split('=')

        if '"' in string:
            # do sumn
            rex = re.search(r"\"(.+)\"", string)
            if not rex: return
            filters[0]["method"] = "eq"
            filters[0]["value"] = rex.group(1)
        elif '=' in string and len(spl) < 2:
            return
        else:
            filters[0]["value"] = spl[-1]
            filters[0]["method"] = "eq" if match_whole_cell else "sub" 

        if '=' in string:
            filters[0]["columns"] = [spl[0].capitalize()]
        else:
            filters[0]["columns"] = df.columns.to_list()

        return self.apply(df, filters, "dependent")

    def join_dataframes(self, tables):
        if not tables:
            return -1
        df = pd.concat(tables, axis=0)
        df.drop_duplicates(subset=["Counter"], inplace=True)
        df.sort_values("Counter", ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def change_dependency(self, dependency):
        self.dependency = dependency
        self._filtered_data = self.apply(self._original_data, self.lst, dependency)
        self.valueUpdated.emit()






class FilterWindow(QWidget):
    closed = pyqtSignal()
    def __init__(self, headers):
        super().__init__()
        # self.model = model
        self.headers = headers
        self.setWindowTitle('Filters')
        self.setMinimumHeight(300)
        self.setMinimumWidth(300)

        self._layout = QStackedLayout()
        self.setLayout(self._layout)
        self.stack = []
        self.view_layout = False
        self.edit_layout = False
        self.filter_edit_list = False
        self.filter_view_list = False
        self.add_tabs = False
        self.state = 0 # 0 for saved and 1 for unsaved changes

        self.pressable_button_style = ""
        self.unpressable_button_style = """
                    QPushButton#ApplyButton {
                        border-color: #777;
                        color: #777;
                    }
                    """

    # def closeEvent(self, a0):
    #     self.closed.emit()
    #     a0.accept()

    def set_model(self, model:FilterModel):
        self.model = model
        
        self.create_add_page()
        self.create_view_page()
        self.create_edit_page()

        self.model.valueUpdated.connect(self.handleFilterUpdate)
    
    def set_headers(self, headers:list):
        self.headers = headers

    def view(self, view):
        i = self.stack.index(view)
        self._layout.setCurrentIndex(i)
        self.show()
        self.activateWindow()

    def create_button_group(self, buttons:list, direction="h", justify="stretch"):
        """ list of 2 value tuples/lists """
        btn_group = QWidget()
        if "v" in direction:
            layout = QVBoxLayout(btn_group)
        else:
            layout = QHBoxLayout(btn_group)

        if justify in ["center", "end"]: layout.addStretch()

        btn_group.setLayout(layout)
        for btn in buttons:
            button = QPushButton(btn[0])
            button.pressed.connect(btn[1])
            if btn[0] == "Apply":
                button.setObjectName("ApplyButton")
                # button.setStyleSheet(self.unpressable_button_style)
            layout.addWidget(button)

        if justify in ["center", "start"]: layout.addStretch()
        return btn_group

    def create_action_buttons(self):
        btns = [
            ('Cancel', self.close),
            ('Ok', self.save_changes),
            ('Apply', self.apply_changes)
            ]
        return self.create_button_group(btns, "h", "end")

    def check_boxes(self, boxes:list):
        """ Handles click on 'All' checkbox """
        bol = boxes[0].isChecked()
        for box in boxes[1:]:
            box.setChecked(bol)
            if bol:
                box.clicked.connect(lambda: boxes[0].setChecked(False))

    def check_if_applicable(self):
        """ Check if new filter is applicable """
        parent = self._layout.currentWidget()
        if not parent: return
        tabs = parent.findChild(QTabWidget)
        curr_tab = tabs.currentWidget()
        if not curr_tab: return
        lines = curr_tab.findChildren(QLineEdit)
        if [line for line in lines if line.text()]:
            self.change_state(1)


    def create_add_page(self):
        widget = QWidget(self)
        main_layout = QVBoxLayout(widget)
        widget.setLayout(main_layout)

        # columns
        main_layout.addWidget(QLabel('Columns:'))
        colist = QWidget()
        colay = QVBoxLayout()
        colist.setLayout(colay)
        main_layout.addWidget(colist)
        checkboxes = []
        for col in ["All", *self.headers]:
            box = QCheckBox(col, colist)
            box.stateChanged.connect(self.check_if_applicable)
            checkboxes.append(box)
            colay.addWidget(box)

        checkboxes[0].clicked.connect(lambda: self.check_boxes(checkboxes))


        # cells
        main_layout.addWidget(QLabel("Match:"))
        
        # input switch
        self.input_switch = QPushButton(widget)
        self.input_switch.setCheckable(True)
        self.input_switch.setText("Date inputs")
        self.input_switch.setChecked(False)
        self.input_switch.pressed.connect(lambda: self.update_add_page_inputs(main_layout))
        main_layout.addWidget(self.input_switch)

        self.create_add_page_tabs(main_layout)

        redir = self.create_button_group([
            ('Clear all', self.clear),
            ('Edit', lambda: self.view("edit")),
            ('View', lambda: self.view("view"))
            ], "h", "stretch")
        main_layout.addWidget(redir)

        btn_group = self.create_action_buttons()
        main_layout.addWidget(btn_group)


        widget.setStyleSheet(self.unpressable_button_style)
        self._layout.addWidget(widget)
        self.stack.append("add")


    def update_add_page_inputs(self, layout):
        if self.input_switch.text() == "Date inputs":
            self.input_switch.setText("Text inputs")
        else:
            self.input_switch.setText("Date inputs")
        self.create_add_page_tabs(layout)


    def create_add_page_tabs(self, parent_layout):
        tabs = QTabWidget()
        if self.add_tabs:
            parent_layout.replaceWidget(self.add_tabs, tabs)
            self.add_tabs.deleteLater()
        else:
            parent_layout.addWidget(tabs)
        self.add_tabs = tabs
        is_date = self.input_switch.text() == "Text inputs"
        fields = []
        # exact
        exact = QWidget()
        exmod = QFormLayout()
        exact.setLayout(exmod)
        exmod.addWidget(QLabel("Matches only cells that have the exact same value as written below."))
        exline = QDateTimeEdit(exact) if is_date else QLineEdit(exact)
        fields.append(exline)
        exmod.addRow('Match:', exline)
        tabs.addTab(exact, "Exact")

        # in
        sub = QWidget()
        submod = QFormLayout()
        sub.setLayout(submod)
        submod.addWidget(QLabel("Matches part of cell value."))
        subline = QDateTimeEdit(sub) if is_date else QLineEdit(sub)
        fields.append(subline)
        submod.addRow('Match:', subline)
        tabs.addTab(sub, "Partial")

        # list
        lis = QWidget()
        limod = QFormLayout()
        lis.setLayout(limod)
        limod.addWidget(QLabel("Matches any value in list. Takes comma separated values."))
        lisline = QDateTimeEdit(lis) if is_date else QLineEdit(lis)
        fields.append(lisline)
        limod.addRow('Match:', lisline)
        tabs.addTab(lis, "List")

        # condition
        cond = QWidget()
        conmod = QFormLayout()
        cond.setLayout(conmod)
        combox = QComboBox()
        combox.addItems(['=', '<', '>', '<=', '>=', '!='])
        conmod.addWidget(QLabel("Matches cells that fits condition."))
        conmod.addRow('Operator:', combox)
        combox.currentTextChanged.connect(self.check_if_applicable)
        conline = QDateTimeEdit(cond) if is_date else QLineEdit(cond)
        fields.append(conline)
        conmod.addRow('Value:', conline)
        tabs.addTab(cond, "Conditional")

        # range
        rng = QWidget()
        rnmod = QFormLayout()
        rng.setLayout(rnmod)
        rnmod.addWidget(QLabel("Matches value in range, including both limits. Only works on numbers and dates."))
        rngline1 = QDateTimeEdit(rng) if is_date else QLineEdit(rng)
        rngline2 = QDateTimeEdit(rng) if is_date else QLineEdit(rng)
        fields.append(rngline1)
        fields.append(rngline2)
        rnmod.addRow('Lower bound:', rngline1)
        rnmod.addRow('Higher bound:', rngline2)
        tabs.addTab(rng, "Range")

        for line in fields:
            if is_date:
                line.dateTimeChanged.connect(self.change_state)
            else:
                line.textChanged.connect(self.change_state)

    def create_view_page(self):
        widget = QWidget(self)
        main_layout = QVBoxLayout(widget)
        widget.setLayout(main_layout)

        # filter view
        self.view_layout = main_layout
        self.create_filter_list("view")
        main_layout.addWidget(self.filter_view_list)


        btn_group = self.create_button_group([
            ('Add new', lambda: self.view("add")),
            ('Clear all', self.clear),
            ('Edit', lambda: self.view("edit"))
            ], "v", "end")
        main_layout.addWidget(btn_group)

        self._layout.addWidget(widget)
        self.stack.append("view")

    def create_edit_page(self):
        widget = QWidget(self)
        main_layout = QFormLayout(widget)
        widget.setLayout(main_layout)

        self.edit_layout = main_layout

        # dependency controls
        radio_btns = QWidget()
        radio_layt = QHBoxLayout(radio_btns)
        radio_btns.setLayout(radio_layt)
        self.dep_rad = QRadioButton("Dependent")
        self.dep_rad.setChecked(True)
        self.dep_rad.toggled.connect(lambda: self.model.change_dependency("dependent"))
        radio_layt.addWidget(self.dep_rad)

        self.ind_rad = QRadioButton("Independent")
        self.ind_rad.toggled.connect(lambda: self.model.change_dependency("independent"))
        radio_layt.addWidget(self.ind_rad)

        self.ind_col_rad = QRadioButton("Independent columns")
        self.ind_col_rad.toggled.connect(lambda: self.model.change_dependency("independent_columns"))
        radio_layt.addWidget(self.ind_col_rad)

        main_layout.addWidget(radio_btns)

        self.create_filter_list("edit")
        main_layout.addWidget(self.filter_edit_list)

        btn_group = self.create_button_group([
            ('Add new', lambda: self.view("add")),
            ('Clear all', self.clear),
            ('View', lambda: self.view("view"))
            ], "v", "end")
        main_layout.addWidget(btn_group)

        btn_group = self.create_action_buttons()
        main_layout.addWidget(btn_group)

        widget.setStyleSheet(self.unpressable_button_style)
        self._layout.addWidget(widget)
        self.stack.append("edit")

    def create_filter_list(self, view):
        widget = QWidget()
        # list_layout = QVBoxLayout(widget) if view == "view" else QFormLayout(widget)
        if view == "view":
            list_layout = QVBoxLayout(widget)
        elif view == "edit":
            list_layout = QFormLayout(widget)
            list_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        widget.setLayout(list_layout)

        # Add rows
        self.keep_alive = []
        for i, filter in enumerate(self.model.get()):
            if view == "view":
                list_layout.addWidget(QLabel(str(filter)))
            elif view == "edit":
                del_btn = self.create_del_btn(filter)
                self.keep_alive.append(del_btn)
                field = QLineEdit(str(filter), widget)
                field.textChanged.connect(self.change_state)
                self.keep_alive.append(field)
                list_layout.addRow(del_btn, field)
                # del_btn.pressed.connect(lambda: list_layout.removeRow(i))

        # /re/place widget in layout
        if view == "view":
            if self.filter_view_list:
                self.view_layout.replaceWidget(self.filter_view_list, widget)
                self.filter_view_list.deleteLater()
            self.filter_view_list = widget
        elif view == "edit":
            if self.filter_edit_list:
                self.edit_layout.replaceWidget(self.filter_edit_list, widget)
                self.filter_edit_list.deleteLater()
            self.filter_edit_list = widget

    def create_del_btn(self, filter):
        del_btn = QPushButton("delete")
        del_btn.setStyleSheet("""
                            QPushButton {
                                background: red;
                                color: white;
                                border-color: white;
                                }
                            """)
        del_btn.pressed.connect(lambda: self.model.remove(filter))
        return del_btn


    def get_form_values(self, page):
        """ """
        widg = self._layout.currentWidget()
        if page == "add":
            # columns
            checkboxes = widg.findChildren(QCheckBox)
            selected_columns = [check.text() for check in checkboxes if check.isChecked()]
            if not selected_columns or "All" in selected_columns:
                selected_columns = self.headers

            # filter
            tabs = widg.findChild(QTabWidget)
            tab_title = tabs.tabText(tabs.currentIndex())
            curr_tab = tabs.currentWidget()
            # print(selected_columns)
            # print(tab_title)
            val = curr_tab.findChild(QLineEdit).text()

            match tab_title:
                case "Exact":
                    method = "eq"
                case "Partial":
                    method = "sub"
                case "List":
                    method = "in"
                    val = self.str_to_list(val)
                case "Conditional":
                    method = curr_tab.findChild(QComboBox).currentText()
                case "Range":
                    method = "rng"
                    chil = curr_tab.findChildren(QLineEdit)
                    val = [chil[0].text(), chil[1].text()]
            new_filter = {
                "columns": selected_columns,
                "method": method,
                "value": val
            }
            return new_filter
        elif page == "edit":
            lines = widg.findChildren(QLineEdit)
            return [eval(line.text()) for line in lines if line.text()]

    def apply_changes(self):
        """ apply, don't close window"""
        if self.state == 0: return
        page = ["add", "view", "edit"][self._layout.currentIndex()]
        vals = self.get_form_values(page)
        print(vals)
        if page == "add":
            self.model.add(vals)
        elif page == "edit":
            self.model.set_filters(vals)
        self.change_state(0)

    def save_changes(self):
        """ apply, close window """
        self.apply_changes()
        self.close()

    def change_state(self, new_state=1):
        """ """
        if self.state == new_state: return # Cancel if no change
        self.state = new_state
        parent = self._layout.currentWidget()
        if not parent: return
        if new_state == 1 or new_state:
            parent.setStyleSheet(self.pressable_button_style)
        else:
            parent.setStyleSheet(self.unpressable_button_style)

    def handleFilterUpdate(self):
        """ Handles changes of filters """
        # opn = self.isVisible()
        # if opn: self.close() 
        self.create_filter_list("view")
        self.create_filter_list("edit")
        # if opn: self.show()

    def clear(self):
        self.model.clear()

    def str_to_list(self, string:str):
        """ comma separated string values to list """
        list1 = string.split(",")
        # for s in list1:
        #     s = s.strip()
        return [s.strip() for s in list1]






# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = FilterWindow()
#     sys.exit(app.exec())