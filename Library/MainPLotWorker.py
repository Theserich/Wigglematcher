from matplotlib import pyplot as plt
from numpy import log, where
from Library.CurveManager import CurveManager
from Library.dataMager import Calculator
from Library.HelperFunctions import fast_random_combinations
from numpy import ones, arange,zeros,nanargmax,diff,split, inf
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib
from Library.timer import timer
matplotlib.use("Qt5Agg")

class MplCanvas(FigureCanvas):
    def __init__(self,curvemanager):
        self.fig, self.ax = plt.subplots(2,sharex=True)
        self.ax2 = self.ax[0].twiny()
        super().__init__(self.fig)
        self.ax[0].set_facecolor('none')
        self.ax[1].set_facecolor('none')
        self.ax[0].tick_params(axis='x', which='both', bottom=False)
        self.fig.subplots_adjust(hspace=0)
        self.calcs = []
        self.curveManager = curvemanager
        self.curves = []
        self.ageplot = False
        self.curveColors = []


    @timer
    def update_plot(self,calcs):
        self.curves = self.curveManager.curves
        self.calcs = calcs
        for ax in self.ax:
            ax.clear()
        #self.clear()
        self.maxx = -inf
        self.minx = inf
        self.maxy = -inf
        self.miny = inf
        for i,curve in enumerate(self.curves):
            if curve == 'None':
                continue
            for calc in self.calcs:
                self.plot_calc(calc,i)
        for i, curve in enumerate(self.curves):
            if curve == 'None':
                continue
            self.plotCurve(curve, color=self.curveColors[i], errorbar=False)
        try:
            self.ax[1].set_xlim(left=self.minx, right=self.maxx)
            self.ax[0].set_ylim(bottom=self.miny, top=self.maxy)
        except:
            pass
        overlap = 5
        ylim = self.ax[0].get_ylim()
        dy = ylim[1] - ylim[0]
        self.ax[0].set_ylim(bottom=ylim[0] - dy * overlap, top=ylim[1])
        ylim = self.ax[1].get_ylim()
        dy = ylim[1] - ylim[0]
        self.ax[1].set_ylim(bottom=ylim[0], top=ylim[1] + dy * overlap)
        xticks = self.ax[1].get_xticks()
        new_tick_locations = arange(-50000, 2000, xticks[1] - xticks[0], dtype=int)
        self.ax2.set_xticks(new_tick_locations)
        self.ax2.set_xticklabels(1950 - new_tick_locations)
        self.ax2.set_xlim(self.ax[0].get_xlim())
        self.ax2.set_xlabel('Year BP')
        self.ax2.xaxis.set_label_position('top')
        self.ax2.spines['bottom'].set_visible(False)
        self.ax[0].set_ylabel('F$^{14}$C')
        self.ax[1].set_ylabel('probability density')
        self.ax[1].set_xlabel('calendaryear')
        self.ax[1].yaxis.set_label_position('right')
        self.ax[1].yaxis.tick_right()
        self.ax[0].legend(frameon=False)
        self.ax[0].spines['bottom'].set_visible(False)
        self.ax[1].spines['top'].set_visible(False)
        self.draw()

    def plotCurve(self, curve, errorbar=False, color='C0'):
        data = self.curveManager.data[curve]
        x = data['calendaryear']
        y = data['fm']
        dy = data['fm_sig']
        if self.ageplot:
            y = -8033*log(y)
            dy = 8033/data['fm']*dy
        self.ax[0].fill_between(x, y - dy, y + dy, color=color, alpha=0.5, lw=0, label=curve)
        indexes = where((x>self.minx) & (x<self.maxx))
        try:
            miny = min(y[indexes]-0.008)
            maxy = max(y[indexes]+0.008)
            self.maxy = max(maxy,self.maxy)
            self.miny = min(miny,self.miny)
        except:
            pass

    def plot_calc(self,calc,index):
        curve = self.curves[index]
        if calc.plotsettings['plotbool'] == False:
            return
        ax0 = self.ax[0]
        ax1 = self.ax[1]
        color = calc.plotsettings['colors'][index]
        rangeadd = 200
        try:
            maxind = nanargmax(calc.data[curve]['probability'])
        except ValueError:
            maxind = None
        if maxind is not None:
            maxyear = calc.data[curve]['tyears'][maxind]
            maxx = max(calc.wiggleyears + maxyear - max(calc.wiggleyears))
            if calc.plotsettings['plotbool']:
                x = calc.wiggleyears + maxyear - max(calc.wiggleyears)
                y = calc.wigglefms
                dy = calc.wigglefms_sig
                if self.ageplot:
                    y = -8033 * log(y)
                    dy = 8033 / calc.wigglefms * dy
                ax0.errorbar(x, y, yerr=dy, capsize=3, color=color, fmt='x',
                               alpha=0.5,label=f'{calc.plotsettings["dataName"]} {curve}')
            ax1.fill_between(calc.data[curve]['tyears'],zeros(len(calc.data[curve]['tyears'])),calc.data[curve]['probability'],alpha=0.5,color=color,lw=0)
            self.maxx = max(self.maxx,maxx+ rangeadd)
            self.minx = min(self.minx,maxx - rangeadd)
        self.plot_percentiles(calc,curve,index)

    def plot_percentiles(self,calc, curve,index):
        data = calc.data[curve]
        ylim = self.ax[1].get_ylim()
        yrange = ylim[1] - ylim[0]
        for percentile in calc.percentiles:
            mask = data[f'{percentile}%range']
            y_lvl = -yrange*0.02
            split_indices = where(diff(mask.astype(int)) != 0)[0] + 1
            x = data['tyears']
            x_segments = split(x, split_indices)
            mask_segments = split(mask, split_indices)
            for x_seg, m_seg in zip(x_segments, mask_segments):
                if all(m_seg):
                    if len(x_seg) == 1:  # If the segment has only one point, mark it
                        self.ax[1].plot([x_seg - 0.5, x_seg + 0.5], [y_lvl, y_lvl], color=calc.plotsettings['colors'][index], lw=3, alpha=0.4)
                    else:
                        self.ax[1].plot([min(x_seg), max(x_seg)], [y_lvl, y_lvl], color=calc.plotsettings['colors'][index], alpha=0.4, lw=3)

class MainPLotWorker(QThread):
    data_ready = pyqtSignal(object)
    def __init__(self):
        super().__init__()
        self.recalc = False

    @timer
    def run(self):
        if self.recalc:
            for calc in self.calcs:
                calc.recalc_all()
        self.data_ready.emit(self.calcs)
        self.recalc = False





