import time

from matplotlib import pyplot as plt
from numpy import log, where, array
from numpy import ones, arange,zeros,nanargmax,diff,split, inf
from matplotlib.figure import Figure
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib
from Library.timer import timer
matplotlib.use("Qt5Agg")


class MainPLotWorker(QThread):
    finished = pyqtSignal(object)
    def __init__(self,datasets,curveManager,curveColors,recalculate=False,recalcindex=None,ageplot=False):
        super().__init__()
        self.recalcindex = recalcindex
        self.curveColors = curveColors
        self.datasets = datasets
        self.ageplot = ageplot
        self.curveManager = curveManager
        self.curves = self.curveManager.curves
        self.calcs = []
        self.recalculate = recalculate
        self.data = {}
        self.data['errorbar'] = []
        self.data['ax0fill'] = []
        self.data['ax1fill'] = []
        self.data['axvline'] = []
        self.data['lines'] = []

    def run(self):
        if self.recalculate and self.recalcindex is None:
            for dataset in self.datasets:
                    dataset.calc.recalc_all()
        elif self.recalculate:
            self.datasets[self.recalcindex].calc.recalc_all()
        for dataset in self.datasets:
            calc = dataset.calc
            self.calcs.append(calc)
        self.update_plot()

    def update_plot(self):
        self.maxx = -inf
        self.minx = inf
        self.maxy = -inf
        self.miny = inf
        for i,curve in enumerate(self.curves):
            if curve is None:
                continue
            for calc in self.calcs:
                self.plot_calc(calc,i)
        for i, curve in enumerate(self.curves):
            if curve is None:
                continue
            self.plotCurve(curve,i, color=self.curveColors[i], errorbar=False)
        self.data['minx'] = self.minx
        self.data['maxx'] = self.maxx
        self.data['miny'] = self.miny
        self.data['maxy'] = self.maxy
        self.finished.emit(self.data)

    def plotCurve(self, curve,index, errorbar=False, color='C0'):
        window_length = self.curveManager.curve_windows[index]

        data = self.curveManager.data[curve]
        x = data[f'calendaryear_{window_length}']
        y = data[f'fm_{window_length}']
        dy = data[f'fm_sig_{window_length}']
        if self.ageplot:
            y = -8033*log(y)
            dy = 8033/data[f'fm_{window_length}']*dy
        self.data['ax0fill'].append({'x':x,'y0':y-dy,'y1':y+dy,'color':color,'label':curve})
        #self.ax[0].fill_between(x, y - dy, y + dy, color=color, alpha=0.5, lw=0, label=curve)
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
        #ax1 = self.ax[1]
        color = calc.plotsettings['colors'][index]
        rangeadd = 60
        try:
            maxind = nanargmax(calc.data[curve]['probability'])
        except ValueError:
            maxind = None
        if maxind is not None and len(calc.wiggleyears)>0:
            maxyear = calc.data[curve]['tyears'][maxind]
            x = calc.wiggleyears + maxyear - max(calc.wiggleyears)
            maxx = max(x)
            minx = min(x)
            if calc.plotsettings['plotbool'] and calc.plotsettings['showfits'][index]:

                y = calc.wigglefms
                dy = calc.wigglefms_sig
                if self.ageplot:
                    y = -8033 * log(y)
                    dy = 8033 / calc.wigglefms * dy
                label = f'{calc.plotsettings["dataName"]} {curve}'
                self.data['errorbar'].append({'x': x, 'y': y, 'yerr': dy, 'color': color, 'label': label})
                #ax0.errorbar(x, y, yerr=dy, capsize=3, color=color, fmt='x',alpha=0.5,label=label)
            self.data['ax1fill'].append({'x':calc.data[curve]['tyears']+calc.shift,'y0':zeros(len(calc.data[curve]['tyears'])),'y1':calc.data[curve]['probability'],'color':color,'label':None})
            #ax1.fill_between(calc.data[curve]['tyears'],zeros(len(calc.data[curve]['tyears'])),calc.data[curve]['probability'],alpha=0.5,color=color,lw=0)
            self.maxx = max(self.maxx,maxx+ rangeadd)
            self.minx = min(self.minx,minx - rangeadd)
        if calc.plotsettings['chronology'] and index == 0  and len(calc.wiggleyears)>0:
            self.data['axvline'].append({'x':max(calc.wiggleyears),'ymax':1,'color':color,'label':None})
            #self.ax[1].axvline(max(calc.wiggleyears),color=color,ymax=0.5)
        if len(calc.wiggleyears)>0:
            self.plot_percentiles(calc,curve,index)

    def plot_percentiles(self,calc, curve,index):
        data = calc.data[curve]
        color = calc.plotsettings['colors'][index]
        #ylim = self.ax[1].get_ylim()
        #yrange = ylim[1] - ylim[0]
        for percentile in calc.percentiles:
            mask = data[f'{percentile}%range']
            y_lvl = 0-0.02*(index+1)
            split_indices = where(diff(mask.astype(int)) != 0)[0] + 1
            x = data['tyears']
            x_segments = split(x, split_indices)
            mask_segments = split(mask, split_indices)
            for x_seg, m_seg in zip(x_segments, mask_segments):
                if all(m_seg):
                    if len(x_seg) == 1:  # If the segment has only one point, mark it
                        self.data['lines'].append({'x':[x_seg - 0.3+calc.shift, x_seg + 0.3+calc.shift],'y':array([index, index]), 'color':color,'label':None})
                        #self.ax[1].plot([x_seg - 0.5, x_seg + 0.5], [y_lvl, y_lvl], color=, lw=3, alpha=0.4)
                        self.maxx = max(self.maxx, x_seg - 0.3+calc.shift)
                        self.minx = min(self.minx, x_seg + 0.3+calc.shift)
                    else:
                        x0 = min(x_seg)+calc.shift
                        x1 = max(x_seg)+calc.shift
                        self.maxx = max(self.maxx, x1)
                        self.minx = min(self.minx, x0)
                        self.data['lines'].append(
                            {'x': [x0,x1], 'y': array([index, index]), 'color': color, 'label': None})
                        #self.ax[1].plot([min(x_seg), max(x_seg)], [y_lvl, y_lvl], color=calc.plotsettings['colors'][index], alpha=0.4, lw=3)





