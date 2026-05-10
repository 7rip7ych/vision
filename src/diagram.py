import sys
import os


from matplotlib import colors
import matplotlib.text


os.environ["QT_API"] = "PyQt6"

from pathlib import Path
import random

from PyQt6 import QtGui
from PyQt6.QtGui import QIcon, QPalette, QTextList
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QAbstractItemModel, QAbstractListModel
from PyQt6.QtWidgets import * # pyright: ignore[reportWildcardImportFromLibrary]
from PyQt6.QtQuickWidgets import QQuickWidget
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import src.file as f
import src.table as t
# import src.tabs as tab
import src.data as d
# import src.filter as flt
import src.warning as w
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import cm
import matplotlib as mpl



class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setStyleSheet("background-color:transparent;")

    def set_transparency(self, trans, part="back"):
        if part in ["back", "both"]:
            self.fig.patch.set_alpha(trans)
            self.fig.set_alpha(trans)
        else:
            self.axes.patch.set_alpha(trans)

    def set_background(self, color:str, part:str="back"):
        if part in ["back", "both"]:
            self.fig.patch.set_color(color)
            self.fig.set_facecolor(color)
        else:
            self.axes.patch.set_color(color)



class Chart(QWidget):

    def __init__(self, type="2d", editable=False):
        super().__init__()
        self.type = type
        if type == "1d":
            self.canvas = MplCanvas(self, width=4, height=4, dpi=100)
        else:
            self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self._plot_ref = None
        self.layt = QVBoxLayout()
        if editable:
            self.toolbar = NavigationToolbar(self.canvas, self)
            self.layt.addWidget(self.toolbar)
            # self.toolbar.setStyleSheet("""
            #     QToolbar {
            #         background: #444;
            #         border: 2px solid black;
            #     }
            # """)
        self.layt.addWidget(self.canvas)
        self.setLayout(self.layt)
        # self.canvas.set_transparency(0.5, "back")
        self.canvas.set_background('#f5f5f5')

    def set_data(self, data):
        self.data = data
        # if self.type != "1d":
        #     self.xdata = data[0]
        #     self.ydata = data[1]
        #     if self.type == "3d":
        #         self.zdata = data[2]
        self.update_plot()

    def update_plot(self):
        if self.type == "1d":
            if isinstance(self.data, pd.DataFrame):
                plot_refs = self.data.plot.pie("count", ax=self.canvas.axes)
            else:
                plot_refs = self.canvas.axes.pie(self.data)
            self._plot_ref = plot_refs
        elif self.type == "2d":
            self.ydata = self.ydata[1:] + [random.randint(0, 10)]

            if self._plot_ref is None:
                plot_refs = self.canvas.axes.plot(self.ydata)
                self._plot_ref = plot_refs[0]
            else:
                self._plot_ref.set_ydata(self.ydata)
        self.canvas.draw()
        # self.show()




class LineChart(Chart):

    def __init__(self):
        super().__init__("2d", False)
        n_data = 5
        self.xdata = list(range(n_data))
        self.ydata = [random.randint(0, 10) for _ in range(n_data)]
        self.update_plot()
        # self.show()




class HistogramChart(Chart):

    def __init__(self, title="histogram", xlabel="Name", ylabel="Count", top:int=0, editable=False, editable_bins=True, click_method=None):
        super().__init__("2d", editable)
        # n_data = 5
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.top = top
        self.click_method = click_method
        self.info_annot = None
        self.info_table = None
        self.canvas.axes.set_title(title)
        self.canvas.axes.set_xlabel(xlabel)
        self.canvas.axes.set_ylabel(ylabel)
        self.setMinimumHeight(300)
        self.setMinimumWidth(400)
        if editable_bins:
            place_holder = QWidget()
            hlayt = QHBoxLayout()
            place_holder.setLayout(hlayt)

            hlayt.addWidget(QLabel("Number of bins: "))
            self.bins_edit = QLineEdit()
            self.bins_edit.setText(str(self.top))
            hlayt.addWidget(self.bins_edit)
            self.bins_edit.textChanged.connect(lambda: self.set_top(self.bins_edit.text()))

            info_icon = QLabel("i") #QPushButton()
            # info_icon.setIcon(QIcon("../UI/images/info_circle_icon.png"))
            # info_icon.setIconSize(QSize(10, 10))
            info_icon.setToolTip("Changes the number of bins shown in the graph. \n0 shows all bins. \nA positive integer n shows the top n bins. \nA negative integer -n shows the bottom n bins.")
            hlayt.addWidget(info_icon)

            self.layt.addWidget(place_holder)

            self.setMinimumHeight(400)
            self.setMinimumWidth(400)

        # self.show()

    def set_data(self, data):
        self.data = data
        self.val_counts = self.data.value_counts()
        self.apply_top()
        self.update_plot()

    def set_top(self, top):
        if not isinstance(top, int):
            try:
                top = int(top)
            except ValueError:
                return
        self.top = top
        self.apply_top()
        self.update_plot()

    def apply_top(self):
        counts = self.val_counts
        if counts.empty:
            self.xvals = []
            self.yvals = []
            return
        if self.top == 0 or not isinstance(self.top, int):
            # All
            counts = counts.sort_index()
        elif self.top > 0:
            # Top
            counts = counts.nlargest(n=self.top)
        elif self.top < 0:
            # Bottom
            counts = counts.nsmallest(n=abs(self.top))

        self.xvals = counts.index.to_list()
        if self.top != 0:
            self.xvals = [f"{val:.0f}" for val in self.xvals]
        self.yvals = counts.values

    def update_plot(self):
        self.canvas.axes.clear()
        self.canvas.axes.set_title(self.title)
        self.canvas.axes.set_xlabel(self.xlabel)
        self.canvas.axes.set_ylabel(self.ylabel)
        # if isinstance(nbins, int) and nbins > 0:
        #     plot_refs = self.canvas.axes.hist(self.data, bins=nbins)
        # else:
        #     plot_refs = self.canvas.axes.hist(self.data)

        plot_refs = self.canvas.axes.bar(self.xvals, self.yvals)
        patchs = plot_refs.patches
        # yvals = plot_refs[0]
        # xvals = plot_refs[1]
        # patchs = plot_refs[2]
        self._plot_ref = patchs
        
        if not len(self.yvals) or not len(self.xvals):
            self.canvas.draw()
            # self.show()
            return
        # color
        fracs = self.yvals / self.yvals.max()
        norm = colors.Normalize(vmin=0, vmax=fracs.max())
        for frac, patch in zip(fracs, patchs):
            col = plt.cm.jet(norm(frac))
            patch.set_facecolor(col)

        # labels
        nbins = len(self.xvals)
        # if self.top != 0 and self.top <= 12:
        #     self.canvas.axes.bar_label(plot_refs)
        # else:
        self.annots = []
        for y, x in zip(self.yvals, self.xvals):
            txt = self.format_labels(x, y)
            annot = self.canvas.axes.annotate(txt, xy=(x, y),
                                                xytext=(0, 25), textcoords='offset points',
                                                horizontalalignment='center',
                                                verticalalignment='top',
                                                fontsize=9,
                                                bbox={'boxstyle': "square,pad=0.1", 'fc': "w", 'ec': "w", 'lw': 0})
            if nbins <= 7:
                annot.set_visible(True)
            else:
                annot.set_visible(False)
            self.annots.append(annot)
        if nbins > 7:
            self.hover_listener = self.canvas.mpl_connect("motion_notify_event", self.onhover)
        if nbins > 30:
            # self.canvas.axes.tick_params('x', labelcolor='none')
            self.canvas.axes.set_xticks(self.xvals, labels=self.xvals, rotation=90, ha="right", rotation_mode="anchor")
        elif nbins > 20:
            self.canvas.axes.set_xticks(self.xvals, labels=self.xvals, rotation=60, ha="right", rotation_mode="anchor")
        elif nbins > 7:
            self.canvas.axes.set_xticks(self.xvals, labels=self.xvals, rotation=30, ha="right", rotation_mode="anchor")
        
        if self.click_method is not None:
            self.click_listener = self.canvas.mpl_connect("button_press_event", self.onclick)

        self.canvas.axes.margins(x=0.025, y=0.2)
        # self.canvas.axes.bbox.padded(1, 1)
        self.canvas.fig.tight_layout()
        self.canvas.draw()
        # self.show()

    def format_labels(self, x, y):
        """ Override to format labels """
        y = y[0] if isinstance(y, (list, tuple, np.ndarray)) else y
        txt = f"{x:.0f}\n{y:.0f}" if self.top == 0 else f"{x}\n{y:.0f}"
        return txt

    def onhover(self, event):
        bars = self._plot_ref if isinstance(self._plot_ref, (list, tuple)) else [self._plot_ref]
        for i, bar in enumerate(bars):
            if bar.contains(event)[0]:
                # print(wedge.get_label())
                self.annots[i].set_visible(True)
                # wedge.set(ec='w', lw=1, ls='-')
                self.canvas.draw_idle()
            else:
                if self.annots[i].get_visible():
                    self.annots[i].set_visible(False)

                    self.canvas.draw_idle()

    def onclick(self, event):
        if self.click_method is None: return
        # show info
        bars = self._plot_ref if isinstance(self._plot_ref, (list, tuple)) else [self._plot_ref]
        if self.info_annot is not None:
            self.info_annot.set_visible(False)
            self.canvas.draw_idle()
        for i, bar in enumerate(bars):
            if bar.contains(event)[0]:
                res = self.click_method(self.xvals[i])
                if res is None: return 
                # create info tooltip for bar
                print(type(res[0]), type(res[1]))
                if not isinstance(res[1], str):
                    print("list")
                    alert = w.DialogWindow("Alert", "You are about to open a window with the system messages related to the given alarm number.\nWould you like to proceed?")
                    if alert.exec():
                        print("yes")
                        if self.info_table is not None:
                            self.info_table.close()
                            self.info_table.deleteLater()
                        tbl = QListWidget()
                        tbl.addItems(res[1])
                        # model = QAbstractItemModel(res[1])
                        # tbl.setModel(model)
                        self.info_table = tbl
                        self.info_table.show()
                        return
                    else:
                        print("no")
                        return
                
                x = self.xvals[i]# if isinstance(self.xvals[i], (int, float)) else int(self.xvals[i])
                y = self.yvals[i]
                self.info_annot = self.canvas.axes.annotate(f"{res[0]}: {res[1]}", xy=(x, y),
                                                xytext=(0.5, 0.95), textcoords="axes fraction",
                                                horizontalalignment='center',
                                                verticalalignment='top',
                                                fontsize=9,
                                                arrowprops={'arrowstyle':"-"},
                                                bbox={'boxstyle': "square,pad=0.3", 'fc': "w", 'ec': "k", 'lw': 0.72},
                                                wrap=True)
                self.info_annot.set_visible(True)
                self.canvas.draw_idle()

    

class SumHistogramChart(HistogramChart):

    def __init__(self, title="histogram", xlabel="Name", ylabel="Sum", top:int=0, editable=False, editable_bins=True, click_method=None, unit='int'):
        ylabel = f"{ylabel} [{unit}]"
        self.unit = unit
        super().__init__(title, xlabel, ylabel, top, editable, editable_bins, click_method)
    
    def set_data(self, data, column1, column2):

        self.data = data
        self.val_counts = d.get_value_sums(data, column1, column2)
        self.apply_top()
        self.update_plot()
    
    def format_labels(self, x, y):
        y = y[0] if isinstance(y, (list, tuple, np.ndarray)) else y
        match self.unit:
            case "int":
                txt = f"{x:.0f}\n{y:.0f}" if self.top == 0 else f"{x}\n{y:.0f}"
            case "float":
                txt = f"{x}\n{y}"
            case "s" | "sec" | "second" | "seconds":
                ftime = d.format_time(y, 's')
                txt = f"{x}\n{ftime}"
            case "m" | "min" | "minute" | "minutes":
                ftime = d.format_time(y, 'm')
                txt = f"{x}\n{ftime}"
            case "h" | "hour" | "hours":
                ftime = d.format_time(y, 'h')
                txt = f"{x}\n{ftime}"
            case _:
                txt = f"{x}\n{y}"
        return txt





class ScatterChart(Chart):

    def __init__(self, title="scatter", editable=False):
        super().__init__("2d", editable)
        # n_data = 5
        self.title = title
        # self.xdata = list(range(n_data))
        # self.ydata = [random.randint(0, 10) for _ in range(n_data)]
        # self.canvas.axes.set_title(title)
        # self.update_plot()
        # self.show()

    def set_data(self, xdata, ydata):
        self.xdata = xdata
        self.ydata = ydata
        self.update_plot()
    
    def update_plot(self):
        # self.ydata = self.ydata[1:] + [random.randint(0, 10)]
        self.canvas.axes.clear()
        self.canvas.axes.set_title(self.title)
        plot_refs = self.canvas.axes.scatter(self.xdata, self.ydata, s=1, alpha=0.5)
        self._plot_ref = plot_refs
        # if self._plot_ref is None:
        #     plot_refs = self.canvas.axes.bar(self.xdata, self.ydata)
        #     self._plot_ref = plot_refs[0]
        # else:
        #     self._plot_ref.set_ydata(self.ydata)
        self.canvas.axes.tick_params('x', rotation=-45)
        self.canvas.draw()
        # self.show()




class PieChart(Chart):

    def __init__(self, title="Donut", slices:int=9, shape="donut", editable=False):
        super().__init__("1d", editable)
        self.max_slices = slices
        self.title = title
        self.shape = shape
        if editable:
            self.action_bar = QWidget()
            hlay = QHBoxLayout()
            self.action_bar.setLayout(hlay)

            # btn1 = QPushButton("pie")
            # btn1.pressed.connect(self.pie)
            # hlay.addWidget(btn1)

            # btn2 = QPushButton("donut")
            # btn2.pressed.connect(self.donut)
            # hlay.addWidget(btn2)

            # btn3 = QPushButton("donut2d")
            # btn3.pressed.connect(self.donut2d)
            # hlay.addWidget(btn3)

            slice_in = QLineEdit(str(self.max_slices))
            slice_in.textChanged.connect(lambda: self.change_max_slices(slice_in.text()))
            hlay.addWidget(slice_in)
            self.layt.addWidget(self.action_bar)
        self.hover_listener = None


    def change_max_slices(self, new_value):
        try:
            self.max_slices = int(new_value)
        except ValueError:
            return
        self.set_data(self._original_data, False)

    def set_data(self, data, raw=True):
        self._original_data = self.calculate_slices(data) if raw else data
        self.data = self.cut_off_data(self._original_data)
        # print(self.data)
        self.labels = self.data.index.to_numpy()
        self.slices = self.data["count"].to_numpy()
        if self.shape == "equal_donut2d":
            self.groups = {
                "0": [self.slices[:20], self.labels[:20]],
                "1": [self.slices[20:40], self.labels[20:40]],
                "2": [self.slices[40:60], self.labels[40:60]],
                "3": [self.slices[60:], self.labels[60:]]
            }
        self.update_plot()

    def calculate_slices(self, data):
        """ Calculate slice sizes from value frequencies. """
        length = data.shape[0]
        data = data.value_counts()
        frame = data.to_frame()
        frame.sort_values("count", ascending=False, inplace=True)
        frame["count"] = frame["count"].apply(lambda x: x / length)
        # frame.rename(columns={"count": "portion"}, inplace=True)
        # if frame.shape[0] > self.max_slices:
        #     df = frame.head(self.max_slices)
        #     others = frame.tail(-self.max_slices)
        #     df2 = pd.DataFrame(data = [others.sum()], index=['Others'])
        #     return pd.concat([df, df2])
        return frame

    def cut_off_data(self, data) -> pd.DataFrame:
        if data.shape[0] > self.max_slices:
            df = data.head(self.max_slices)
            others = data.tail(-self.max_slices)
            df2 = pd.DataFrame(data = [others.sum()], index=['Others'])
            return pd.concat([df, df2])
        return data

    def update_plot(self):
        match self.shape:
            case "donut":
                self.donut()
            case "pie":
                self.pie()
            case "equal_donut2d":
                self.equal_donut2d()
            case "donut2d":
                self.donut2d()
        self.canvas.draw()
        # self.show()

    def pie(self):
        self.canvas.axes.clear()

        ref = self.canvas.axes.pie(self.slices, autopct=lambda pct: f"{pct:.1f}%",
                                        textprops=dict(color="w"))
        wedges = ref[0]
        self._plot_ref = wedges
        self.canvas.axes.legend(wedges, self.labels,
                title="labels",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1))

        # self.canvas.setp(autotexts, size=8, weight="bold")

        self.canvas.axes.set_title(self.title)

        self.canvas.draw()
        # self.show()

    def donut(self):
        self.canvas.axes.clear()
        ref = self.canvas.axes.pie(self.slices, wedgeprops=dict(width=0.5), startangle=0)
        wedges = ref[0]
        self._plot_ref = wedges
        if len(wedges) > 9:
            wedges[-1].set_facecolor('0.6')

        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"),
                bbox=bbox_props, zorder=0, va="center")

        self.canvas.axes.legend(wedges, self.labels,
                title="labels",
                loc="center right",
                bbox_to_anchor=(1.5, 0, 0.5, 1))
        self.annots = []
        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1)/2. + p.theta1
            if ang == 0 or ang == 180:
                ang += 0.1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            annot = self.canvas.axes.annotate(f"{self.labels[i]}\n~{self.slices[i]*100:.2f}%", xy=(x, y),
                                                xytext=(1.35*np.sign(x), 1.4*y),
                                                horizontalalignment=horizontalalignment, **kw)
            annot.set_visible(False)
            self.annots.append(annot)
            p.set(ec='w', lw=1, ls='-')

        self.hover_listener = self.canvas.mpl_connect("motion_notify_event", self.hover)
        self.canvas.axes.set_title(self.title)

        self.canvas.draw()
        # self.show()

    def donut2d(self):
        self.canvas.axes.clear()
        size = 0.3
        vals = np.array([[60., 32.], [37., 40.], [29., 10.]])
        tab20c = plt.color_sequences["tab20c"]
        outer_colors = [tab20c[i] for i in [0, 4, 8]]
        inner_colors = [tab20c[i] for i in [1, 2, 5, 6, 9, 10]]

        self.canvas.axes.pie(vals.sum(axis=1), radius=1, colors=outer_colors,
            wedgeprops=dict(width=size, edgecolor='w'))

        self.canvas.axes.pie(vals.flatten(), radius=1-size, colors=inner_colors,
            wedgeprops=dict(width=size, edgecolor='w'))

        self.canvas.axes.set(aspect="equal", title='Pie plot with `ax.pie`')
        self.canvas.axes.set_title(self.title)
        self.canvas.draw()
        # self.show()

    def equal_donut2d(self, group=None):
        self.shape = "equal_donut2d"
        self.canvas.axes.clear()
        size3 = 0.3
        size2 = 0.3
        size1 = 0.2
        if not self.colors:
            self.colors = {
                "1": {
                    "default": '#010633',
                    "active": '#010633',
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
        if group is None:
            outer_slices = np.concatenate([val[0] for val in self.groups.values()])
            outer_labels = np.concatenate([val[1] for val in self.groups.values()])
        else:
            outer_slices = self.groups[group][0]
            outer_labels = self.groups[group][1]
        # slc = np.empty(self.slices.shape) if group is None else np.empty(self.groups[str(group)][0].shape)
        # slc.fill(1)

        ref_outer = self.canvas.axes.pie(outer_slices, wedgeprops=dict(width=size3, edgecolor=self.colors["3"]["edge"], facecolor=self.colors["3"]["default"]), 
                                         startangle=90, radius=1)
        wedges = ref_outer[0]

        inner_slices = []
        inner_labels = []
        for key, val in self.groups.items():
            if len(val[0]) == 0:
                continue
            inner_slices.append(len(val[0]))
            inner_labels.append(key)


        # ref_inner = self.canvas.axes.pie(np.array([len(grp[0]) for grp in self.groups.values()]), labels=list(self.groups.keys()), labeldistance=0.7,
        #                                  wedgeprops=dict(width=size2, edgecolor=self.colors["2"]["edge"], facecolor=self.colors["2"]["default"]), 
        #                                  startangle=90, radius=1-size3, textprops=dict(color=self.colors["2"]["text"]))
        
        ref_inner = self.canvas.axes.pie(inner_slices, wedgeprops=dict(width=size2, edgecolor=self.colors["2"]["edge"], facecolor=self.colors["2"]["default"]), 
                                         startangle=90, radius=1-size3, textprops=dict(color=self.colors["2"]["text"]))
        
        ref_core = self.canvas.axes.pie(np.array([1]), wedgeprops=dict(width=size1, edgecolor=self.colors["1"]["edge"], facecolor=self.colors["1"]["default"]), 
                                        startangle=90, radius=1-size3-size2)
        
        self._plot_ref = [ref_core[0], ref_inner[0], ref_outer[0]]
        

        # outer labels
        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"),
                bbox=bbox_props, zorder=5, va="center")

        # self.canvas.axes.legend(wedges, self.labels,
        #         title="labels",
        #         loc="center left",
        #         bbox_to_anchor=(1, 0, 0.5, 1))

        self.annots_outer = []
        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1)/2. + p.theta1
            if ang == 0 or ang == 180:
                ang += 0.1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"

            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            # j = i if group is None else i + int(group)*20
            annot = self.canvas.axes.annotate(self.format_outer_labels(outer_labels[i]), xy=(x, y),
                                                xytext=(1.1*np.sign(x), 1.1*y),
                                                horizontalalignment=horizontalalignment, fontsize='small', wrap=True, **kw)
            annot.set_visible(False)
            self.annots_outer.append(annot)
            p.set(ec='w', lw=1, ls='-')

        # labels inner
        self.annots_inner = []
        inner_radius = 1-size3-(size2/2)
        for i, p in enumerate(ref_inner[0]):
            ang = (p.theta2 - p.theta1)/2. + p.theta1
            if ang == 0 or ang == 180:
                ang += 0.1
            y = np.sin(np.deg2rad(ang)) * inner_radius
            x = np.cos(np.deg2rad(ang)) * inner_radius
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"

            # kw["arrowprops"].update({"connectionstyle": connectionstyle})
            # j = i if group is None else i + int(group)*20
            annot = self.canvas.axes.annotate(self.format_inner_labels(inner_labels[i]), xy=(x, y),
                                                horizontalalignment=horizontalalignment, fontsize='medium', wrap=True, bbox=bbox_props, zorder=5, va="center")
            annot.set_visible(False)
            self.annots_inner.append(annot)
            p.set(ec='w', lw=1, ls='-')

        self.hover_listener = self.canvas.mpl_connect("motion_notify_event", self.hover)
        self.canvas.axes.set_title(self.title)

        self.canvas.draw()
        # self.show()

    def format_inner_labels(self, label):
        """ Placeholder function """
        return f"{label}"

    def format_outer_labels(self, label):
        """ Placeholder function """
        return f"{label}"


    def hover(self, event):
        if self.shape == "equal_donut2d":
            found = False
            # first layer
            core = self._plot_ref[0][0] if isinstance(self._plot_ref[0], (list, tuple)) else self._plot_ref[0]
            second_layer = self._plot_ref[1] if isinstance(self._plot_ref[1], (list, tuple)) else [self._plot_ref[1]]
            third_layer = self._plot_ref[2] if isinstance(self._plot_ref[2], (list, tuple)) else [self._plot_ref[2]]
            if core.contains(event)[0]:
                core.set(fc=self.colors["1"]["active"])
                found = True
            else:
                core.set(fc=self.colors["1"]["default"])

            # second layer
            for i, inner in enumerate(second_layer):
                if inner.contains(event)[0]:
                    found = True
                    inner.set(fc=self.colors["2"]["active"])
                    self.annots_inner[i].set_visible(True)
                    inner.set(ec=None, lw=None)
                else:
                    if self.annots_inner[i].get_visible():
                        inner.set(fc=self.colors["2"]["default"])
                        self.annots_inner[i].set_visible(False)

                        inner.set(ec='w', lw=1, ls='-')
                    #inner.set(fc=self.colors["2"]["default"])

            # third layer
            for i, wedge in enumerate(third_layer):
                if wedge.contains(event)[0]:
                    found = True
                    wedge.set(fc=self.colors["3"]["active"])
                    # print(wedge.get_label())
                    self.annots_outer[i].set_visible(True)
                    wedge.set(ec=None, lw=None)
                    wedge.set_radius(1.05)
                else:
                    if self.annots_outer[i].get_visible():
                        wedge.set(fc=self.colors["3"]["default"])
                        self.annots_outer[i].set_visible(False)

                        wedge.set(ec='w', lw=1, ls='-')
                        wedge.set_radius(1)
            self.canvas.draw_idle()
        else:
            for i, wedge in enumerate(self._plot_ref):
                if wedge.contains(event)[0]:
                    # print(wedge.get_label())
                    self.annots[i].set_visible(True)
                    # wedge.set(ec='w', lw=1, ls='-')
                    wedge.set(ec=None, lw=None)
                    wedge.set_radius(1.05)
                    self.canvas.draw_idle()
                else:
                    if self.annots[i].get_visible():
                        self.annots[i].set_visible(False)
                        
                        wedge.set(ec='w', lw=1, ls='-')
                        # wedge.set(ec=None, lw=None)
                        wedge.set_radius(1)
                        self.canvas.draw_idle()

        # if event.inaxes == self.canvas.axes:
        #     self.annots[0].set_visible(False)
        #     self.canvas.draw_idle()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    test_data = pd.DataFrame({"col1": [1, 2, 3, 4, 5], "col2": [5, 4, 5, 6, 5]}, index=[0, 1, 2, 3, 4])
    hist = HistogramChart()
    hist.set_data(test_data)
    sys.exit(app.exec())