import sys
import os
from datetime import datetime

os.environ["QT_API"] = "PyQt6"

from pathlib import Path
import random
import re

from PyQt6 import QtGui
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QPixmap, QPicture, QImage, QAction, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, QDate, QTimeZone
from PyQt6.QtWidgets import * # pyright: ignore[reportWildcardImportFromLibrary]
from PyQt6.QtQuickWidgets import QQuickWidget
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import src.file as f
# import src.tabs as tab
# import src.data as d
# import src.filter as flt
import src.diagram as dia
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages


class NavDonut(dia.PieChart):
    
    focusChanged = pyqtSignal()
    def __init__(self):
        super().__init__("Nav", 1000, "equal_donut2d", False)
        self.current_group = None
        self.current_zone = None
        self.colors = {
            "1": {
                "default": '#010633',
                "active": "#030A49",
                "inactive": '#737c9e',
                "edge": 'w'
            },
            "2": {
                "default": '#071278',
                "active": '#0d1eba',
                "inactive": "#50566e",
                "edge": 'w',
                "text": 'w'
            },
            "3": {
                "default": '#4664db',
                "active": '#214eff',
                "inactive": '#737c9e',
                "edge": 'w'
            }
        }
        self.canvas.set_transparency(0.8, "back")
        self.canvas.set_background("#006effff")
    
    def equal_donut2d(self):
        super().equal_donut2d(self.current_group)
        self.click_listener = self.canvas.mpl_connect("button_press_event", self.onclick)
        self.leave_listener = self.canvas.mpl_connect("figure_leave_event", self.onleave)
        self.leave_listener = self.canvas.mpl_connect("axes_leave_event", self.onleave)
    
    def set_data(self, data, raw=True):
        # self._original_data = self.calculate_slices(data) if raw else data
        # self.data = self.cut_off_data(self._original_data)
        # # print(self.data)
        # self.labels = self.data.index.to_numpy()
        # self.slices = self.data["count"].to_numpy()
        # if self.shape == "equal_donut2d":
        #     self.groups = {
        #         "0": [self.slices[:20], self.labels[:20]],
        #         "1": [self.slices[20:40], self.labels[20:40]],
        #         "2": [self.slices[40:60], self.labels[40:60]],
        #         "3": [self.slices[60:], self.labels[60:]]
        #     }
        self.groups = {}
        for grp in data["Group"].unique():
            zones = data[data["Group"] == grp]["Zone"].unique()
            slc = np.empty(len(zones))
            slc.fill(1)
            self.groups[grp] = [slc, zones]
        self.slices = np.concatenate([val[0] for val in self.groups.values()])
        self.labels = np.concatenate([val[1] for val in self.groups.values()])
        # print(self.groups)
        self.update_plot()

    def underscore_label_to_list(self, label, trim=["line", "zone"]):
        arr = label.split("_")
        if arr[0].lower() in trim:
            arr.pop(0)
        return arr

    def format_inner_labels(self, label, long=False):
        """ Remove 'line' from label """
        arr = self.underscore_label_to_list(label, ["line"])
        return f"{' '.join(arr)}" if long else f"{arr[0]}"

    def format_outer_labels(self, label, long=False):
        """ Remove 'zone' from label """
        arr = self.underscore_label_to_list(label)
        return f"{' '.join(arr)}" if long else f"{arr[0]}"


    def hover(self, event):
        found = False
        # first layer
        # if not isinstance(self._plot_ref[0], list) or not isinstance(self._plot_ref[1], list): return
        core = self._plot_ref[0][0] if isinstance(self._plot_ref[0], (list, tuple)) else self._plot_ref[0]
        second_layer = self._plot_ref[1] if isinstance(self._plot_ref[1], (list, tuple)) else [self._plot_ref[1]]
        third_layer = self._plot_ref[2] if isinstance(self._plot_ref[2], (list, tuple)) else [self._plot_ref[2]]
        if core.contains(event)[0]:
            self.onleave(None)
            core.set(fc=self.colors["1"]["active"])
            found = True
        else:
            core.set(fc=self.colors["1"]["default"])

        # second layer
        for i, inner in enumerate(second_layer):
            if inner.contains(event)[0]:
                found = True
                inner.set(fc=self.colors["2"]["active"])
                inner.set(fc=self.colors["2"]["active"])
                self.annots_inner[i].set_visible(True)
                inner.set(ec=None, lw=None)
                if self.current_group != None:
                    # a group selected
                    curr = (self.current_group == list(self.groups.keys())[i]) # if hovered group is selected
                    for outer in third_layer:
                        outer.set(fc=self.colors["3"]["default" if curr else "inactive"])
                else:
                    # no group selected
                    for j, outer in enumerate(third_layer):
                        if self.labels[j] in self.groups[list(self.groups.keys())[i]][1]:
                            outer.set(fc=self.colors["3"]["default"])
                        else:
                            outer.set(fc=self.colors["3"]["inactive"])
                self.canvas.draw_idle()
            else:
                if self.annots_inner[i].get_visible():
                        inner.set(fc=self.colors["2"]["default"])
                        self.annots_inner[i].set_visible(False)

                        inner.set(ec='w', lw=1, ls='-')

        if found:
            for i, inner in enumerate(second_layer):
                if not inner.contains(event)[0]:
                    inner.set(fc=self.colors["2"]["default"])
            self.canvas.draw_idle()
            # return
        
        # third layer
        for i, wedge in enumerate(third_layer):
            if wedge.contains(event)[0]:
                found = True
                wedge.set(fc=self.colors["3"]["active"])
                # print(wedge.get_label())
                self.annots_outer[i].set_visible(True)
                # wedge.set(ec='w', lw=1, ls='-')
                wedge.set(ec=None, lw=None)
                wedge.set_radius(1.05)
                self.canvas.draw_idle()
            else:
                if self.annots_outer[i].get_visible():
                    wedge.set(fc=self.colors["3"]["default"])
                    self.annots_outer[i].set_visible(False)

                    wedge.set(ec='w', lw=1, ls='-')
                    # wedge.set(ec=None, lw=None)
                    wedge.set_radius(1)
                    self.canvas.draw_idle()
        # if not found: self.onleave(None)


    def onclick(self, event):
        """ Handles mouse presses on canvas. """
        if event.button == 3:
            return self.onrightclick(event)
        found = False
        # print(event)
        core = self._plot_ref[0][0] if isinstance(self._plot_ref[0], (list, tuple)) else self._plot_ref[0]
        second_layer = self._plot_ref[1] if isinstance(self._plot_ref[1], (list, tuple)) else [self._plot_ref[1]]
        third_layer = self._plot_ref[2] if isinstance(self._plot_ref[2], (list, tuple)) else [self._plot_ref[2]]
        if core.contains(event)[0]:
            self.change_group(None)
            return

        for i, inner in enumerate(second_layer):
            if inner.contains(event)[0]:
                found = True
                # print(inner, i)
                self.change_group(i)
                inner.set(fc=self.colors["2"]["default"])
                for outer in third_layer:
                    outer.set(fc=self.colors["3"]["default"])
            else:
                inner.set(fc=self.colors["2"]["inactive"])
            self.canvas.draw_idle()
        if found: return
        
        for i, wedge in enumerate(third_layer):
            # if not wedge.get_visible(): continue
            if wedge.contains(event)[0]:
                # print(wedge, i)
                self.change_zone(i)

    def onrightclick(self, event):
        core = self._plot_ref[0][0] if isinstance(self._plot_ref[0], (list, tuple)) else self._plot_ref[0]
        second_layer = self._plot_ref[1] if isinstance(self._plot_ref[1], (list, tuple)) else [self._plot_ref[1]]
        third_layer = self._plot_ref[2] if isinstance(self._plot_ref[2], (list, tuple)) else [self._plot_ref[2]]
        if core.contains(event)[0]:
            return

        for i, inner in enumerate(second_layer):
            if inner.contains(event)[0]:
                group = list(self.groups.keys())[i]
                old_text = self.annots_inner[i].get_text()
                new_text = self.format_inner_labels(group, (self.format_inner_labels(group, True) != old_text))
                self.annots_inner[i].set_text(new_text)
                self.canvas.draw_idle()
                return

        for i, wedge in enumerate(third_layer):
            # if not wedge.get_visible(): continue
            if wedge.contains(event)[0]:
                # print(wedge, i)
                zone = self.groups[self.current_group][1][i] if self.current_group else self.labels[i]
                old_text = self.annots_outer[i].get_text()
                new_text = self.format_outer_labels(zone, (self.format_outer_labels(zone, True) != old_text))
                self.annots_outer[i].set_text(new_text)
                self.canvas.draw_idle()
                return

    def onleave(self, event):
        if isinstance(self._plot_ref[0], list):
            for outer in self._plot_ref[0]:
                outer.set(fc=self.colors["3"]["default"])
        if isinstance(self._plot_ref[1], list):
            for inner in self._plot_ref[1]:
                inner.set(fc=self.colors["2"]["default"])

    def change_zone(self, zone):
        if zone != None and isinstance(zone, int):
            # zone = self.annots[zone].get_text()
            # zone = zone.split("\n")[0]
            zone = self.groups[self.current_group][1][zone] if self.current_group else self.labels[zone]

        self.current_zone = zone
        print("set zone ", zone)
        self.focusChanged.emit()

    def change_group(self, group):
        print("changing group to ", group)
        self.current_group = list(self.groups.keys())[group] if isinstance(group, int) else group
        self.equal_donut2d()
        self.change_zone(None)


class AutoscalePixmap(QLabel):
    def __init__(self, source):
        super().__init__()
        self.pmap = QPixmap(source)
        self.set()

    def set(self):
        w = self.width()
        h = self.height()
        new_map = self.pmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(new_map)

    def resizeEvent(self, a0):
        self.set()


class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Analysis')
        self.setMinimumHeight(300)
        self.setMinimumWidth(400)
        self.setGeometry(500, 100, 1300, 800)
        
        # self.setStyle("Fusion")
        self.background_style = "QWidget { color: #000; }" \
        "QMainWindow, QToolButton { background-color: #fff; border-radius: 10px; }" \
        "QMenuBar, QToolBar { background-color: #ddd; color: #000; }" \
        "QToolBar QWidget { background-color: transparent }"
        self.layer1_style = """
        QWidget { background-color: #dedede; color: #000; border-radius: 10px; }
        QTabWidget { border-radius: initial; }
        QLineEdit { 
            background-color: #fefefe;
            border-radius: 2px;
            padding: 2px 4px;
            border-bottom: 1px solid #777;
        }
        """

        self.tabs_style = """
        QWidget { background-color: #dedede; color: #000;}
        QTabBar { background-color: transparent; }

        QTabBar::tab 
        {
            background: #ccc;
            color: #444;
            padding: 2px 8px;
            border: 1px solid #bbb;
            border-bottom: 0;
            margin: 0px 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }

        QTabBar::tab:selected, 
        QTabBar::tab:hover 
        {
            border-color: #c2c2c2;
            color: black;
            background: #dedede; 
        }
        QLineEdit {
            background-color: #fefefe;
            border-radius: 2px;
            padding: 2px 4px;
            border-bottom: 1px solid #777;
        }

        """
        self.layer2_style = "QWidget { background-color: #ccc; }"
        self.setStyleSheet(self.background_style)
        self.start_date = None
        self.end_date = None
        self.alarm_info = None
        self.independent = False
        self.reload_button = None
        self.data = None
        self._original_data = None
        self.table_data = None
        self._focus_data = None
        self.export_window = None
        self.draw()
        # self.show()

    def closeEvent(self, a0):
        self.hide()
        a0.ignore()

    def draw(self):

        # Nav
        self.nav = NavDonut()
        self.nav.focusChanged.connect(self.change_target)
        self.nav.canvas.set_transparency(0, "both")
        self.nav.canvas.set_background('None')

        self.draw_info_box()

        # main container
        self.main_tabs = QTabWidget()
        # pal = self.main_tabs.palette()
        # pal.setColor(self.main_tabs.foregroundRole(), QColor("#dedede"))
        # self.main_tabs.setPalette(pal)
        # self.main_tabs.setAutoFillBackground(True)
        self.main_tabs.setStyleSheet(self.tabs_style)
        self.draw_tab1()
        self.draw_tab2()
        self.draw_tab3()
        # self.draw_tab4()
        self.draw_tab5()
        # # main sublayer
        # self.main_tabs.addTab(self.graph_tab1, "Overview")
        self.create_menu()
        self.create_bottom_toolbar()
        # main layer
        self.place_holder = QWidget()
        self.grid = QGridLayout()
        self.place_holder.setLayout(self.grid)
        self.setCentralWidget(self.place_holder)
        self.grid.addWidget(self.nav, 0, 0, 2, 1)
        self.grid.addWidget(self.info_box, 2, 0, 3, 1)
        self.grid.addWidget(self.main_tabs, 0, 1, 5, 4)
        self.info_box.setStyleSheet(self.layer1_style)

        self.figures = {
            "1.1 Pie": self.msg_pie,
            "1.2 Scatter": self.scatter_chart,
            "1.3 Scatter duration": self.duration_chart,
            "2.1 Bar machine count": self.hist_chart1,
            "2.2 Bar system count": self.hist_chart2,
            "2.3 Bar all count": self.hist_chart3,
            "3.1 Bar machine sum": self.tab3_hist1,
            "3.2 Bar system sum": self.tab3_hist2,
            "3.3 Bar all sum": self.tab3_hist3,
        }

    def create_menu(self):
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        exp_act = QAction("Export", self)
        exp_act.setStatusTip("Export analysis")
        exp_act.triggered.connect(self.export)
        self.toolbar.addAction(exp_act)

    def create_bottom_toolbar(self):
        """ Bottom bar """
        self.status_bar = self.statusBar()
        if self.status_bar is None:
            self.status_bar = QStatusBar(self)
        # self.dependency_switch = QCheckBox("Independent")
        # self.dependency_switch.stateChanged.connect(lambda: self.change_dependency(self.dependency_switch.isChecked()))
        # self.status_bar.addWidget(self.dependency_switch)

        
        self.draw_reload_button(False)

    def draw_reload_button(self, enabled=False):
        if self.reload_button is None:
            self.reload_button = QToolButton()
            self.reload_button.setText("Refresh")
            self.reload_button.setIcon(QIcon("UI/images/refresh.svg"))
            self.reload_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            self.reload_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            # self.reload_button.setContentsMargins(1, 0, 0, 0)
            self.reload_button.pressed.connect(self.refresh)
            self.status_bar.addPermanentWidget(self.reload_button) if self.status_bar is not None else self.grid.addWidget(self.reload_button, 5, 5)
        self.reload_button.setEnabled(enabled)
        if enabled:
            self.reload_button.setStyleSheet("QToolButton { color: #000; border: 1px outset #999; padding-left: 5px; } QIcon { opacity: 1; }")
        else:
            self.reload_button.setStyleSheet("QToolButton { color: #888; border: 1px solid #eee; padding-left: 5px; } QIcon { opacity: 0.5; }")

    def minimum_time_input(self, action):
        holder = QWidget()
        hlayout = QHBoxLayout()
        holder.setLayout(hlayout)
        hlayout.addWidget(QLabel("Minimum duration (seconds): "))
        self.timediff_limit = QLineEdit()
        self.timediff_limit.setText("0")
        self.timediff_limit.textChanged.connect(action)
        hlayout.addWidget(self.timediff_limit)
        return holder

    def refresh(self):
        self.set_data(self.table_data)
        self.draw_reload_button(False)

    def draw_info_box(self):
        # info box
        self.info_box = QWidget()
        self.info_box_layout = QVBoxLayout()
        self.info_box.setLayout(self.info_box_layout)
        fnt = QFont("Ubuntu Mono", 9, QFont.Weight.Normal)
        fnt.setStyleHint(QFont.StyleHint.Monospace)
        # print(QFontDatabase.families())
        self.info_box.setFont(fnt)
        self.info_box_rows = {
            "title": QLabel("Title here"),
            "machine_count": QLabel("Machine row count: "),
            "system_count": QLabel("System row count: "),
            "total_count": QLabel("Total row count: "),
            "alarms": QLabel("Different alarms: "),
            "time": QLabel("Total time: ")
        }
        for label in self.info_box_rows.values():
            self.info_box_layout.addWidget(label)
        # self.info_box_layout.addWidget()
        # self.info_box_layout.addWidget(QLabel("Title here"))
        self.info_box_layout.addStretch()

        self.info_box_layout.addWidget(self.minimum_time_input(self.update_figures))
        # date input
        date_form = QWidget()
        date_form_layout = QFormLayout(date_form)
        # date_form.setLayout(date_form_layout)
        date_form.setStyleSheet("""
                                QWidget { background: #f5f5f5; }
                                QPushButton {
                                    background: #eee;
                                    border: 2px outset #ccc;
                                    padding: 2px 8px;
                                    border-radius: 0;
                                }
                                QPushButton:hover {
                                    background: #e5e5e5;
                                }
                                """)
        self.info_box_layout.addWidget(date_form)
        date_form_layout.addWidget(QLabel("Time frame:"))

        self.start_date_edit = QDateTimeEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate(2015, 1, 1))
        # self.start_date_edit.dateTimeChanged.connect(self.change_timeframe)
        # self.info_box_layout.addWidget(self.start_date_edit)
        date_form_layout.addRow("Start", self.start_date_edit)

        self.end_date_edit = QDateTimeEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate(2050, 1, 1))
        # self.end_date_edit.dateTimeChanged.connect(self.change_timeframe)
        # self.info_box_layout.addWidget(self.end_date_edit)
        date_form_layout.addRow("End", self.end_date_edit)

        btn_grp = QWidget(date_form)
        grp_layout = QHBoxLayout(btn_grp)
        date_form_layout.addWidget(btn_grp)
        self.clear_date_inputs = QPushButton("Clear")
        self.clear_date_inputs.pressed.connect(self.reset_timeframe)
        grp_layout.addWidget(self.clear_date_inputs)
        grp_layout.addStretch()

        self.apply_date_inputs = QPushButton("Apply")
        self.apply_date_inputs.pressed.connect(self.change_timeframe)
        grp_layout.addWidget(self.apply_date_inputs)


    def draw_tab1(self):
        # first tab
        self.graph_tab1 = QWidget()
        self.graph_tab1_layout = QGridLayout()
        self.graph_tab1.setLayout(self.graph_tab1_layout)

        # graphs
        self.msg_pie = dia.PieChart("MsgNr")
        self.nav.canvas.set_transparency(0, "both")
        self.nav.canvas.set_background('None')

        self.scatter_chart = dia.ScatterChart("Appearance")

        self.duration_chart = dia.ScatterChart("Duration")


        # second sublayer
        self.graph_tab1_layout.addWidget(self.msg_pie, 0, 0, 1, 2)
        self.graph_tab1_layout.addWidget(self.scatter_chart, 1, 0)
        self.graph_tab1_layout.addWidget(self.duration_chart, 1, 1)

        # main sublayer
        self.main_tabs.addTab(self.graph_tab1, "Overview")

    def draw_tab2(self):
        self.graph_tab2 = QWidget()
        grid = QGridLayout(self.graph_tab2)

        scroll_area = QScrollArea(self.graph_tab2)
        scroll_area.setWidgetResizable(True)
        # scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        grid.addWidget(scroll_area, 0, 0)

        scroll_content = QWidget()
        self.graph_tab2_layout = QGridLayout(scroll_content)

        scroll_area.setWidget(scroll_content)

        # self.graph_tab2 = QWidget()
        # self.graph_tab2_layout = QGridLayout()
        # self.graph_tab2.setLayout(self.graph_tab2_layout)
        
        self.hist_chart1 = dia.HistogramChart("Machine", "MsgNr", top=10, click_method=self.get_alarm_info)

        self.hist_chart2 = dia.HistogramChart("System", "MsgNr", top=10, click_method=self.get_alarm_info)

        self.hist_chart3 = dia.HistogramChart("All", "MsgNr", top=15, click_method=self.get_alarm_info)

        # holder = QWidget()
        # hlayout = QHBoxLayout()
        # holder.setLayout(hlayout)
        # hlayout.addWidget(QLabel("Minimum duration (seconds): "))
        # self.tab2_timediff_limit = QLineEdit()
        # self.tab2_timediff_limit.setText("0")
        # self.tab2_timediff_limit.textChanged.connect(self.update_tab2)
        # hlayout.addWidget(self.tab2_timediff_limit)

        # self.hist_chart3 = dia.HistogramChart("Alarm count", "MsgNr")
        # self.hist_chart3.canvas.set_transparency(0.5, "back")
        # self.hist_chart3.canvas.set_background(background)

        # self.graph_tab2_layout.addWidget(holder, 0, 0)
        self.graph_tab2_layout.addWidget(self.hist_chart1, 1, 0)
        self.graph_tab2_layout.addWidget(self.hist_chart2, 2, 0)
        self.graph_tab2_layout.addWidget(self.hist_chart3, 3, 0)
        

        self.main_tabs.addTab(self.graph_tab2, "Alarm")

    def draw_tab3(self):
        self.graph_tab3 = QWidget()
        grid = QGridLayout(self.graph_tab3)

        scroll_area = QScrollArea(self.graph_tab3)
        scroll_area.setWidgetResizable(True)

        # scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        # scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        grid.addWidget(scroll_area, 0, 0)

        scroll_content = QWidget()
        self.graph_tab3_layout = QGridLayout(scroll_content)

        scroll_area.setWidget(scroll_content)

        self.tab3_hist1 = dia.SumHistogramChart("Machine", "MsgNr", top=10, unit="s", click_method=self.get_alarm_info)
        # self.tab3_hist1.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # self.tab3_hist1.setDisabled(True)

        self.tab3_hist2 = dia.SumHistogramChart("System", "MsgNr", top=10, unit="s", click_method=self.get_alarm_info)

        self.tab3_hist3 = dia.SumHistogramChart("All", "MsgNr", top=15, unit="s", click_method=self.get_alarm_info)

        # holder = QWidget()
        # hlayout = QHBoxLayout()
        # holder.setLayout(hlayout)
        # hlayout.addWidget(QLabel("Minimum duration (seconds): "))
        # self.tab3_timediff_limit = QLineEdit()
        # self.tab3_timediff_limit.setText("0")
        # self.tab3_timediff_limit.textChanged.connect(self.update_tab3)
        # hlayout.addWidget(self.tab3_timediff_limit)

        # self.graph_tab3_layout.addWidget(holder, 0, 0)
        self.graph_tab3_layout.addWidget(self.tab3_hist1, 1, 0)
        self.graph_tab3_layout.addWidget(self.tab3_hist2, 2, 0)
        self.graph_tab3_layout.addWidget(self.tab3_hist3, 3, 0)

        self.main_tabs.addTab(self.graph_tab3, "Duration")

    def draw_tab4(self):
        self.graph_tab4 = QWidget()
        self.graph_tab4_layout = QGridLayout()
        self.graph_tab4.setLayout(self.graph_tab4_layout)

        self.main_tabs.addTab(self.graph_tab4, "Timeline")
    
    def draw_tab5(self):
        self.tab5 = QWidget()
        self.tab5_layout = QGridLayout()
        self.tab5.setLayout(self.tab5_layout)

        img = AutoscalePixmap("./UI/images/line.png")#QLabel(self.tab5)
        # pmap =QPixmap("./UI/images/line.png")
        # img.setPixmap(pmap)

        # self.tab5.resizeEvent.connect(lambda: self.scale_pixmap(pmap, img))
        # img2 = QLabel().setPicture(QPicture("./UI/images/line.png"))
        self.tab5_layout.addWidget(img, 0, 0)
        # self.tab5_layout.addWidget(img2, 1, 0)

        self.main_tabs.addTab(self.tab5, "Line")


    def update_info(self):
        """ Update info in info_box """
        group = self.nav.current_group if self.nav.current_group else "All"
        zone = self.nav.current_zone if self.nav.current_zone else "All"
        self.info_box_rows["title"].setText(f"Group: {group}\nZone: {zone}")
        self.info_box_rows["title"].setStyleSheet("QLabel { font-weight: 600; font-size: 16px; }")
        
        mach = self._focus_data[self._focus_data["Class"] != 34]
        syst = self._focus_data[self._focus_data["Class"] == 34]
        only2 = self._focus_data_only_2
        self.info_box_rows["machine_count"].setText(f"""{'Machine row count: ':<20}{f'{mach.shape[0]} ({mach[mach["State"] == 2].shape[0]} U rows)':>30}""")
        self.info_box_rows["system_count"].setText(f"""{'System row count: ':<20}{f'{syst.shape[0]} ({syst[syst["State"] == 2].shape[0]} U rows)':>30}""")
        self.info_box_rows["total_count"].setText(f"""{'Total row count: ':<20}{f'{self._focus_data.shape[0]} ({only2.shape[0]} U rows)':>30}""")
        self.info_box_rows["alarms"].setText(f"""{'Different alarms: ':<20}{f'{self._focus_data["MsgNr"].nunique()}':>30}""")
        self.info_box_rows["time"].setText(f"""{'Total time: ':<20}{f'{only2["TimeDiff"].sum()/3600:.2f} h':>30}""")

        if self._focus_data is not None and "DateTime" in self._focus_data.columns:
            startdt = str(self._focus_data["DateTime"].min())
            enddt = str(self._focus_data["DateTime"].max())
            strt = QDateTime.fromString(startdt, Qt.DateFormat.ISODateWithMs)
            end = QDateTime.fromString(enddt, Qt.DateFormat.ISODateWithMs)
            end = end.addSecs(60)
            self.start_date_edit.setDateTime(strt)
            self.end_date_edit.setDateTime(end)


    def update_tab1(self):
        # tab 1
        only2 = self._focus_data_only_2
        self.msg_pie.set_data(only2["MsgNr"])
        # min_diff = only2["TimeDiff"].apply(lambda x: x//60*5)
        # self.duration_chart.set_data(min_diff)
        self.duration_chart.set_data(only2["TimeDiff"].index.to_list(), only2["TimeDiff"].to_list())

        self.scatter_chart.set_data(only2["DateTime"].to_list(), only2["MsgNr"].to_list())

    def update_tab2(self):
        # tab 2
        only2 = self._focus_data_only_2
        min_timediff = 0
        mindiff_text = self.timediff_limit.text()
        try:
            min_timediff = int(mindiff_text)
        except ValueError:
            min_timediff = 0
        only2_long = only2[only2["TimeDiff"] >= min_timediff]
        long_nr = only2_long[only2_long["MsgNr"] > 1000000]
        short_nr = only2_long[only2_long["MsgNr"] < 1000000]
        # short1 = short_nr[short_nr["MsgNr"] <= 2000]
        # short2 = short_nr[short_nr["MsgNr"] > 2000]
        self.hist_chart1.set_data(short_nr["MsgNr"])
        self.hist_chart2.set_data(long_nr["MsgNr"])
        self.hist_chart3.set_data(only2_long["MsgNr"])

    def update_tab3(self):
        """ Tab 3 """
        only2 = self._focus_data_only_2
        min_timediff = 0
        mindiff_text = self.timediff_limit.text()
        try:
            min_timediff = int(mindiff_text)
        except ValueError:
            min_timediff = 0
        only2_long = only2[only2["TimeDiff"] > min_timediff]
        long_nr = only2_long[only2_long["MsgNr"] > 1000000]
        short_nr = only2_long[only2_long["MsgNr"] < 1000000]
        # short1 = short_nr[short_nr["MsgNr"] <= 2000]
        # short2 = short_nr[short_nr["MsgNr"] > 2000]
        self.tab3_hist1.set_data(short_nr, "MsgNr", "TimeDiff")
        self.tab3_hist2.set_data(long_nr, "MsgNr", "TimeDiff")
        self.tab3_hist3.set_data(only2_long, "MsgNr", "TimeDiff")

    def update_tab4(self):
        """"""

    def update_figures(self):
        self._focus_data_only_2 = self._focus_data[self._focus_data["State"] == 2]
        self.update_tab1()
        self.update_tab2()
        self.update_tab3()
        self.update_tab4()

        self.nav.set_data(self.data[["Zone", "Group"]])
        self.update_info()

    def load_data(self, data):
        # if not self.isVisible(): return
        if data is None or data.empty: return
        self.draw_reload_button(False)
        self._original_data = data
        self.table_data = data
        self.set_data(data)
        # self.update_figures()
        # self.show()

    def set_data(self, data):
        self.data = data
        self._focus_data = data
        self.change_target()

    def load_info(self, info:pd.DataFrame):
        self.alarm_info = info

    def change_timeframe(self):
        self.start_date = self.start_date_edit.dateTime()
        self.end_date = self.end_date_edit.dateTime()
        self.change_target()

    def reset_timeframe(self):
        """ Reset date filters """
        if not isinstance(self._original_data, pd.DataFrame): return
        startdt = str(self._original_data["DateTime"].min())
        enddt = str(self._original_data["DateTime"].max())
        strt = QDateTime.fromString(startdt, Qt.DateFormat.ISODateWithMs)
        end = QDateTime.fromString(enddt, Qt.DateFormat.ISODateWithMs)
        end = end.addSecs(60)
        self.start_date_edit.setDateTime(strt)
        self.end_date_edit.setDateTime(end)
        self.change_timeframe()
    
    def table_changed(self, data):
        """ Create reload button """
        self.table_data = data
        if self.data is None and not data.empty:
            self.data = data
            self._focus_data = data
        # elif self.reload_button is None:
        #     return
        else:
            self.draw_reload_button(True)

    def change_dependency(self, state:bool):
        self.independent = state

    def open_and_load(self, data):
        self.load_data(data)
        self.show()

    def change_target(self):
        zone = self.nav.current_zone
        group = self.nav.current_group
        if zone != None:
            self._focus_data = self.data[self.data["Zone"] == zone]
        elif group != None:
            self._focus_data = self.data[self.data["Zone"].astype("str").isin(self.nav.groups[group][1])]
        else:
            self._focus_data = self.data

        if self.start_date is not None:
            start = datetime.fromtimestamp(self.start_date.toSecsSinceEpoch())
            self._focus_data = self._focus_data[self._focus_data["DateTime"] >= start]
        if self.end_date is not None:
            end = datetime.fromtimestamp(self.end_date.toSecsSinceEpoch())
            self._focus_data = self._focus_data[self._focus_data["DateTime"] <= end]
        self.update_figures()
    
    def get_alarm_info(self, nr):
        try:
            nr = int(nr)
        except ValueError:
            return
        # print(nr)
        df = self.alarm_info
        if df is None or df.empty: return
        # check what the message number column is called
        identifier = ""
        if "NR" in df.columns:
            identifier = "NR"
        elif "ID" in df.columns:
            identifier = "ID"
        elif "MsgNr" in df.columns:
            identifier = "MsgNr"

        # try:
        row = df[df[identifier] == nr]
        if row.empty:
            rows = self.data[self.data["MsgNr"] == nr]
            classes = rows["Class"].unique()
            messages = rows["Text1"].unique()
            # print(classes)
            # print(messages)
            return [classes, messages]
        else:
            row.reset_index(inplace=True)
            cls = row.at[0, "Classname"]
            msg = row.at[0, "Text1"]
            # print(cls, msg)
            return [cls, msg]
        # except KeyError:
        #     return
    
    def export(self):
        """ Export graphs """
        if self.export_window is None or not isinstance(self.export_window, ExportWindow):
            self.export_window = ExportWindow(self)
        self.export_window.show()

class ExportWindow(QWidget):
    def __init__(self, parent:AnalysisWindow):
        super().__init__()
        self.pare = parent
        self.setWindowTitle("Export settings")
        self.setMinimumWidth(300)
        self.lay = QGridLayout(self)

        self.left = QWidget()
        self.left_layout = QVBoxLayout(self.left)

        self.left_layout.addWidget(QLabel("Select which graphs to export:"))
        # checklist = QWidget()
        # checklay = QVBoxLayout()
        # checklist.setLayout(colay)
        # self.left_layout.addWidget(colist)
        self.checkboxes = []
        for fig in ["All", *list(self.pare.figures.keys())]:
            box = QCheckBox(fig, self.left)
            self.checkboxes.append(box)
            self.left_layout.addWidget(box)

        self.checkboxes[0].clicked.connect(lambda: self.check_boxes(self.checkboxes))



        self.right = QWidget()
        self.right_layout = QVBoxLayout(self.right)
        # right.setLayout(self.right_layout)
        
        self.right_layout.addStretch()
        self.name_field = QLineEdit(self)
        self.right_layout.addWidget(QLabel("Enter a filename:"))
        self.right_layout.addWidget(self.name_field)

        radio_btns = QWidget()
        radio_layt = QHBoxLayout(radio_btns)
        radio_btns.setLayout(radio_layt)
        self.radio1 = QRadioButton("PDF (.pdf)")
        radio_layt.addWidget(self.radio1)

        self.radio2 = QRadioButton("Image (.png)")
        self.radio2.setChecked(True)
        radio_layt.addWidget(self.radio2)

        self.radio3 = QRadioButton("Vector (.svg)")
        radio_layt.addWidget(self.radio3)

        self.right_layout.addWidget(radio_btns)

        self.sep_box = QCheckBox("Collective", self.right)
        self.right_layout.addWidget(self.sep_box)

        self.right_layout.addStretch()

        self.submit_button = QPushButton("Save")
        self.submit_button.pressed.connect(self.execute)
        self.right_layout.addWidget(self.submit_button)

        self.lay.addWidget(self.left, 0, 0)
        self.lay.addWidget(self.right, 0, 1)

    def check_boxes(self, boxes:list):
        """ Handles click on 'All' checkbox """
        bol = boxes[0].isChecked()
        for box in boxes[1:]:
            box.setChecked(bol)
            if bol:
                box.clicked.connect(lambda: boxes[0].setChecked(False))

    def get_selected_type(self):
        if self.radio1.isChecked():
            return "pdf"
        if self.radio2.isChecked():
            return "png"
        if self.radio3.isChecked():
            return "svg"

    def execute(self):
        name = self.name_field.text()
        file_type = self.get_selected_type()
        settings = {
            "format": file_type,
            "collective": self.sep_box.isChecked()
        }
        selected_figs = [check.text() for check in self.checkboxes if check.isChecked()]
        if not selected_figs or "All" in selected_figs:
            selected_figs = list(self.pare.figures.keys())
        self.export_to_file(name, settings, selected_figs)
        self.hide()

    def export_to_file(self, filename, settings:dict, elements:list=[], filedir=None):
        if "." in filename:
            filename = re.sub(r"\..*$", "", filename)
        if not filedir:
            path = str(Path.home() / "Downloads" / filename)
        else:
            path = filedir + "/" + filename

        if not settings["collective"]:
            for fig in elements:
                nm = filename + "-" + fig.replace(" ", "_").replace(".", "-")
                if not filedir:
                    path = str(Path.home() / "Downloads" / nm)
                else:
                    path = filedir + "/" + nm
                self.pare.figures[fig].canvas.fig.savefig(path, facecolor='w', transparent=False, format=settings["format"])
                return "ok"
        else:
            path = str(Path.home() / "Downloads" / filename) if not filedir else filedir + "/" + filename
            
            # pdf
            with PdfPages(path) as pdf:
                for fig in elements:
                    pdf.savefig(self.pare.figures[fig].canvas.fig)
            return "ok"
                
        # match settings["format"]:
        #     case "pdf" | "PDF" | ".pdf":
        #         if "." not in filename:
        #             path = path + ".xlsx"
        #         elif ".csv" not in filename:
        #             path = re.sub(r"\..*$", ".xlsx", path)
        #     case "img" | "png" | ".png":
        #         if "." in filename:
        #             filename = re.sub(r"\..*$", "", path)
        #         for fig in elements:
        #             nm = filename + "-" + fig.replace(" ", "_").replace(".", "-")
        #             if not filedir:
        #                 path = str(Path.home() / "Downloads" / nm)
        #             else:
        #                 path = filedir + "/" + nm
        #             self.pare.figures[fig].canvas.fig.savefig(path, facecolor='w', transparent=False)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = AnalysisWindow()
    w.show()
    sys.exit(app.exec())
