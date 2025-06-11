import time
import io
from matplotlib import pyplot as plt
from Library.dataMager import Calculator
from Library.HelperFunctions import fast_random_combinations
from numpy import ones, arange, zeros, cumsum, inf, searchsorted, max as npmax, argsort
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from Library.comset import read_settings, write_settings
import matplotlib
from PyQt5.QtCore import QTimer
from Library.timer import timer

matplotlib.use("Qt5Agg")
from matplotlib.figure import Figure


class PlotWindow_test(QMainWindow):
    """A separate window to display each Matplotlib graph."""

    def __init__(self, calc: Calculator, curveind=0, plotButton="consitencyPLotButton"):
        super().__init__()

        self.windowName = plotButton
        self.loadSize()
        self.setWindowTitle("Matplotlib Graph")
        self.show()
        self.raise_()
        setattr(self, f"plot_window_{id(self)}", self)

        self.timer = QTimer()
        self.calc = calc
        self.curve = self.calc.curves[curveind]
        self.plotButton = plotButton
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        for spine in ["top", "left", "right"]:
            self.ax.spines[spine].set_visible(False)
        self.ax.set_yticks([])
        self.ax.xaxis.grid()
        self.ax.set_xlabel("calendaryear")
        self.ax.set_ylim(top=1.05, bottom=0)
        self.ax.set_title(self.curve)
        self.fig.set_constrained_layout(False)
        self.ax.set_rasterization_zorder(1)

        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)  # Add the toolbar on top
        layout.addWidget(self.canvas)  # Add the canvas
        central_widget = QWidget()
        if (
            self.windowName == "consitencyPLotButton"
            or self.windowName == "consitencyPLotButton2"
        ):
            self.plotConsistency()
        elif (
            self.plotButton == "individualPLotButton"
            or self.plotButton == "individualPLotButton2"
        ):
            self.plotIndividual()
        self.canvas.draw()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def loadSize(self):
        settings = read_settings(self.windowName)
        if settings is not None:
            h = settings["windowheight"]
            w = settings["windowwidth"]
            self.resize(w, h)
        else:
            self.setGeometry(200, 200, 700, 500)

    def closeEvent(self, event):
        w = self.width()
        h = self.height()
        settings = {}
        settings["windowheight"] = h
        settings["windowwidth"] = w
        pos = self.pos()
        settings["posx"] = pos.x()
        settings["posy"] = pos.y()
        self.timer.stop()
        write_settings(settings, self.windowName)
        super().closeEvent(event)

    def plotConsistency(self):
        self.timer = QTimer()
        self.pt = self.calc.data[self.curve]["probability"]
        self.ps = self.calc.data[self.curve]["ps"][self.calc.wiggledata["active"]]
        self.slice = get_indexes(self.ps)
        self.years = self.calc.data[self.curve]["tyears"][self.slice]
        self.lenx = len(self.slice)
        self.N = len(self.ps)
        self.i = 0
        self.j = 0
        self.indexes = list(arange(self.N))
        self.combis = {}
        self.h = {}
        self.timer.timeout.connect(self.animate_step_cons)
        self.timer.start(60)  # ~30 FPS

    def animate_step_cons(self):
        nplot = 100

        h = ones(self.lenx) * (self.N - self.i - 1) / self.N * 1
        self.combis.setdefault(
            self.i, fast_random_combinations(self.indexes, self.i + 1, 20)
        )
        combis = self.combis[self.i]
        # self.ax.plot(self.years, h,color='k',alpha=0.1)
        for combi in combis:
            ptic = 1
            for index in combi:
                prob = self.ps[index][self.slice]
                ptic *= prob
            # ptic = ptic / sum(ptic)
            ptic = ptic / max(ptic)
            plotptic = ptic / self.N
            n = min(len(combis), nplot)
            self.ax.plot(
                self.years, plotptic + h, alpha=min(1 / n * 1.05, 0.9), color="k"
            )

            # self.ax.fill_between(self.years, h, plotptic + h, color='k', alpha=min(1 / n * 1.05, 0.9), lw=0)

            # print(len(combis))
            if self.j >= len(combis) - 1:
                self.j = 0
                self.i += 1
            else:
                self.j += 1
        if self.i >= self.N:
            self.timer.stop()
        self.canvas.draw_idle()

    def animate_step(self):
        dt = self.dts[self.i]
        hplus = (self.N - self.i) / self.N * 1
        height = (self.N - self.i - 1) / self.N * 1
        h = ones(self.lenx) * height
        p = self.ps[self.i][self.slice]
        ploti = p / self.maxp / self.N
        self.ax.fill_between(
            self.years + dt, h, self.pt + h, color="k", alpha=0.9, lw=0
        )
        self.ax.fill_between(self.years + dt, h, ploti + h, color="k", alpha=0.5, lw=0)
        print(hplus - height)
        self.ax.text(
            self.minx,
            (height + hplus) / 2,
            f"{self.labels[self.i]} Agreement: {self.agreements[self.i]*100: .1f} %",
            ha="left",
            va="top",
            fontsize=(hplus - height) * 500,
        )
        self.canvas.draw_idle()
        self.i += 1
        if self.i >= self.N:
            self.timer.stop()

    def plotIndividual(self):
        self.timer = QTimer()

        self.ps = self.calc.data[self.curve]["ps"][self.calc.wiggledata["active"]]
        self.slice = get_indexes(self.ps)
        self.pt = self.calc.data[self.curve]["probability"][self.slice]
        self.years = self.calc.data[self.curve]["tyears"][self.slice]
        self.dts = self.calc.wiggledata["year"][self.calc.wiggledata["active"]] - max(
            self.calc.wiggledata["year"][self.calc.wiggledata["active"]]
        )
        sortind = argsort(self.dts)
        self.dts = self.dts[sortind]
        self.ps = self.ps[sortind]
        self.minx = min(self.years + min(self.dts))
        self.maxp = npmax(self.ps)
        self.maxpt = npmax(self.pt)
        self.i = 0
        self.N = len(self.ps)
        self.pt = self.pt / max(self.pt) / self.N
        if "label" in self.calc.wiggledata:
            self.labels = self.calc.wiggledata["label"][self.calc.wiggledata["active"]][
                sortind
            ]
        else:
            self.labels = self.calc.wiggledata["year"][self.calc.wiggledata["active"]][
                sortind
            ]
        self.agreements = self.calc.wiggledata[f"{self.curve}A_i"][
            self.calc.wiggledata["active"]
        ]
        agreement = self.calc.wiggledata["year"][self.calc.wiggledata["active"]]
        self.lenx = len(self.slice)
        self.timer.timeout.connect(self.animate_step)
        self.timer.start(30)


def get_indexes(ps):
    lower = inf
    upper = -inf
    for p in ps:
        cdf = cumsum(p)
        lower_idx = searchsorted(cdf, (1 - 0.999) / 2)
        lower = min(lower, lower_idx)
        upper_idx = searchsorted(cdf, 1 - (1 - 0.999) / 2)
        upper = max(upper, upper_idx)
    indices = arange(lower, upper + 1)
    return indices
