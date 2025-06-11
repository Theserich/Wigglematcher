import time
import io
from matplotlib import pyplot as plt
from Library.dataMager import Calculator
from Library.HelperFunctions import fast_random_combinations
from numpy import ones, arange,zeros, cumsum,inf,searchsorted, max as npmax, argsort
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow,QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from Library.comset import read_settings, write_settings
import matplotlib
from Library.timer import timer
matplotlib.use("Qt5Agg")
from matplotlib.figure import Figure

class PlotWindow(QMainWindow):
    """A separate window to display each Matplotlib graph."""
    def __init__(self, fig,windowName):
        super().__init__()
        self.windowName = windowName
        self.loadSize()
        self.setWindowTitle("Matplotlib Graph")
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)  # Add the toolbar on top
        layout.addWidget(self.canvas)  # Add the canvas
        central_widget = QWidget()
        self.canvas.draw()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)



    def loadSize(self):
        settings = read_settings(self.windowName)
        if settings is not None:
            h = settings['windowheight']
            w = settings['windowwidth']
            self.resize(w, h)
        else:
            self.setGeometry(200, 200, 700, 500)

    def closeEvent(self, event):
        w = self.width()
        h = self.height()
        settings = {}
        settings['windowheight'] = h
        settings['windowwidth'] = w
        pos = self.pos()
        settings['posx'] = pos.x()
        settings['posy'] = pos.y()
        write_settings(settings, self.windowName)
        super().closeEvent(event)

class PLotWorker(QThread):
    progress = pyqtSignal(list)
    finished = pyqtSignal(object)
    def __init__(self, calc: Calculator, curveind = 0, plotButton='consitencyPLotButton'):
        super().__init__()
        self.calc = calc
        self.curve = self.calc.curves[curveind]
        self.plotButton = plotButton

    def run(self):
        if self.plotButton == 'consitencyPLotButton'or self.plotButton == 'consitencyPLotButton2':
            self.plotConsistency()
        elif self.plotButton == 'individualPLotButton' or self.plotButton == 'individualPLotButton2':
            self.plotIndividual()
        else:
            return
        self.finished.emit((self.fig, self.plotButton))


    def plotConsistency(self):
        self.fig = Figure(dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(self.curve)
        ps = self.calc.data[self.curve]['ps'][self.calc.wiggledata['active']]
        slice = get_indexes(ps)
        years = self.calc.data[self.curve]['tyears'][slice]
        lenx = len(slice)
        self.figdata = {}
        self.figdata['x'] = years
        N = len(ps)
        indexes = list(arange(N))
        for i, p in enumerate(ps):
            self.figdata[i] = {}
            h = ones(lenx) * (N - i - 1) / N * 1
            percentage = int(100 / N * i)

            combis = fast_random_combinations(indexes, i + 1, 50)
            for j, combi in enumerate(combis):
                ptic = 1
                for index in combi:
                    prob = ps[index][slice]
                    ptic *= prob
                ptic = ptic / sum(ptic)
                plotptic = ptic/ N# / max(ptic)

                nplot = 100
                if j < nplot:
                    n = min(len(combis), nplot)
                    #self.figdata[i][j] = {'y':plotptic+h,'y0':h,'alpha':min(1 / n * 1.05, 0.9)}
                    self.ax.fill_between(years, h, plotptic + h, color='k', alpha=min(1 / n * 1.05, 0.9), lw=0)
                    #self.ax.fill_between(years, h, plotptic + h, color='k', alpha=min(1 / n * 1.05, 0.9), lw=0)
            self.progress.emit([percentage,self.plotButton])
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['top'].set_visible(False)
        self.ax.set_yticks([])
        self.ax.set_xlabel('calendaryear')
        self.ax.set_ylim(top=1,bottom=0)


    def plotIndividual(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(self.curve)
        pt = self.calc.data[self.curve]['probability']
        agreements = self.calc.wiggledata[f'{self.curve}A_i'][self.calc.wiggledata['active']]
        ps = self.calc.data[self.curve]['ps'][self.calc.wiggledata['active']]
        indexes = get_indexes(ps)
        years = self.calc.data[self.curve]['tyears'][indexes]

        dts = self.calc.wiggledata['year'][self.calc.wiggledata['active']]-max(self.calc.wiggledata['year'])
        sortind = argsort(dts)
        dts = dts[sortind]
        ps = ps[sortind]


        minx = min(years+min(dts))-50
        maxp = npmax(ps)
        maxpt = npmax(pt)
        N = len(ps)
        pt = pt[indexes] / max(pt)/N
        if 'label' in self.calc.wiggledata:
            labels = self.calc.wiggledata['label'][self.calc.wiggledata['active']][sortind]
        else:
            labels = self.calc.wiggledata['year'][self.calc.wiggledata['active']][sortind]
        agreements = self.calc.wiggledata[f'{self.curve}A_i'][self.calc.wiggledata['active']][sortind]
        lenx = len(indexes)
        y0 = self.ax.transData.transform((0, 0))[1]
        y1 = self.ax.transData.transform((0, 1/N))[1]
        pixel_height = abs(y1 - y0)
        fontsize_points = (pixel_height* 1* 72) / self.fig.dpi

        for i, p in enumerate(ps):
            dt = dts[i]
            percentage = int(100 / N * i)
            ploti = p[indexes]/maxp/N
            h = (N - i - 1) / N * 1
            hplus =  (N - i) / N * 1
            harr = ones(lenx) * h
            self.ax.fill_between(years+dt, harr, pt + h, color='k', alpha=0.9, lw=0)
            self.ax.fill_between(years+dt, harr, ploti + h, color='k', alpha=0.5, lw=0)
            self.ax.text(minx,(h+hplus)/2,f'{labels[i]} Agreement: {agreements[i]*100: .1f} %', ha='left', va='top',fontsize = min(fontsize_points,12))
            self.progress.emit([percentage, self.plotButton])
        self.ax.set_ylim(top=1.05)
        self.ax.set_yticks([])
        self.ax.spines['left'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['top'].set_visible(False)
        self.ax.xaxis.grid()



def get_indexes(ps):
    lower= inf
    upper = -inf
    for p in ps:
        cdf = cumsum(p)
        lower_idx = searchsorted(cdf, (1 - 0.999) / 2)
        lower = min(lower,lower_idx)
        upper_idx = searchsorted(cdf, 1 - (1 - 0.999) / 2)
        upper = max(upper,upper_idx)
    indices = arange(lower, upper + 1)
    return indices





