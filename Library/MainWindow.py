from PyQt5.uic import loadUi

from pathlib import Path
import os
from matplotlib.axis import Axis
from Library.comset import read_settings, write_settings
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QFileDialog, QColorDialog
from PyQt5.Qt import Qt
from PyQt5.QtCore import QItemSelectionModel
from matplotlib.pyplot import Figure
from Library.dataSetManager import DataSetManager
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas,NavigationToolbar2QT as NavigationToolbar
from matplotlib import pyplot as plt
from Library.timer import timer
from numpy import where, zeros, argmax,append, log, exp, arange,diff,ones,split, inf
from Library.CurveManager import CurveManager
from Library.MainPlotThread import MainPLotWorker
import matplotlib
from Library.ExcelWorker import ExcelWorker
matplotlib.use("Qt5Agg")
from copy import copy


class WidgetMain(QMainWindow):
    def __init__(self, path):
        self.plotFms = False
        self.starfolder = 'Library\\Settings\\'
        self.settings = read_settings('display_settings')
        super(WidgetMain, self).__init__()
        loadUi(path, self)
        self.curveManager = CurveManager()
        self.load_settings()
        self.Ncurves = 2
        for i in range(self.Ncurves):
            self.__dict__[f'curveBox{i}'].addItem('None')
            self.__dict__[f'colorbutton{i}'].clicked.connect(self.open_color_dialog)
            self.__dict__[f'colorbutton{i}'].setStyleSheet(f"background-color: {self.curveColors[i]};")
            self.__dict__[f'spinBox{i}'].valueChanged.connect(self.change_displayed_curve_version)
            self.__dict__[f'spinBox{i}'].hide()
        for curve in self.curveManager.data:
            for i in range(self.Ncurves):
                self.__dict__[f'curveBox{i}'].addItem(curve)
        for i,curve in enumerate(self.curveManager.curves):
            index = self.__dict__[f'curveBox{i}'].findText(curve)
            if index != -1:  # -1 means not found
                self.__dict__[f'curveBox{i}'].setCurrentIndex(index)
        #self.update_plot()
        self.ageBox.stateChanged.connect(self.changeToAge)
        self.addDatasetButton.clicked.connect(self.addDataset_tab)
        self.showButton.clicked.connect(self.redraw)
        self.actionLoad_in_Curve.triggered.connect(self.load_Oxcal_curve)
        self.actionLoad_in_curve_from_xlsx.triggered.connect(lambda: self.curveManager.load_excel_curve(self))
        self.actionSave_results_to_xlsx.triggered.connect(self.saveData)
        for i in range(self.Ncurves):
            self.__dict__[f'curveBox{i}'].currentIndexChanged.connect(self.changeCurves)
        self.recalcFlag = False
        self.recalcIndex = None
        self.threads = []
        self.redraw()

    def changeCurves(self):
        for i in range(self.Ncurves):
            curve = self.__dict__[f'curveBox{i}'].currentText()
            self.curveManager.curves[i] = curve
            for dataset in self.datasets:
                dataset.calc.curves[i] = curve
        self.recalcFlag = True
        self.redraw()

    def change_displayed_curve_version(self):
        for i in range(self.Ncurves):
            window_length = self.__dict__[f'spinBox{i}'].value()
            self.curveManager.curve_windows[i] = window_length
            testkey = f'calendaryear_{window_length}'
            for curve in self.curveManager.curves:
                if curve != 'None':
                    data =  self.curveManager.data[curve]
                    if testkey not in data:
                        self.curveManager.generate_averaged_curves(curve, window_length)
        self.redraw()

    def addDataset_tab(self):
        tabs = self.tabWidget.count()
        self.datasets.append(DataSetManager(self,tabs))
        self.tabWidget.setCurrentIndex(tabs)
        self.redraw()

    def open_color_dialog(self):
        color = QColorDialog.getColor()
        widget = self.sender()
        button = widget.objectName()
        index = int(button[-1])
        if color.isValid():  # Ensure a valid color is selected
            widget.setStyleSheet(f"background-color: {color.name()};")
            self.curveColors[index] = color.name()
            self.redraw()


    def initialize_plot(self):
        p = self.widget.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)
        self.plot_layout = QVBoxLayout(self.widget)
        self.ax = []
        self.figure, ax = plt.subplots(1)
        self.ax.append(ax)
        self.ax.append(ax.twinx())
        self.canvas = FigureCanvas(self.figure)
        #self.ax2 = self.ax[0].twiny()
        self.errorbarlines = []
        self.vlines = []
        self.figure.subplots_adjust(hspace=-1)
        #self.ax2.set_xlim(self.ax[0].get_xlim())
        #self.ax2.set_xlabel('Year BP')
        #self.ax2.xaxis.set_label_position('top')
        #self.ax2.spines['bottom'].set_visible(False)
        self.ax[0].set_facecolor('none')
        self.ax[1].set_facecolor('none')
        self.ax[0].tick_params(axis='x', which='both', bottom=False)
        self.ax[1].set_xlabel('calendaryear')
        self.ax[0].set_ylabel('F$^{14}$C')
        self.ax[1].yaxis.set_label_position('right')
        self.ax[1].set_ylabel('probability density')
        self.ax[1].yaxis.tick_right()
        self.ax[0].spines['bottom'].set_visible(False)
        self.ax[1].spines['top'].set_visible(False)
        self.addToolBar(Qt.BottomToolBarArea, NavigationToolbar(self.canvas, self))
        self.plot_layout.addWidget(self.canvas)

    def initialize_plot2(self):
        p = self.widget.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)
        self.plot_layout = QVBoxLayout(self.widget)
        self.canvas = None
        #self.addToolBar(Qt.BottomToolBarArea, NavigationToolbar(self.canvas, self))
        self.plot_layout.addWidget(self.canvas)


    def changeToAge(self):
        for dataset in self.datasets:
            dataset.tableModel.updateHeader()
        self.redraw()

    def figure_updated(self,dataset):
        for errorbar in self.errorbarlines:
            errorbar.set_label(None)
        self.errorbarlines = []
        for vline in self.vlines:
            vline.remove()
        self.vlines = []
        for x in self.ax:
            for line in x.lines[:]:
                try:
                    line.remove()
                except ValueError:
                    pass
            for line in self.errorbarlines:
                for bar in line[1]:
                    bar.remove()
            for collection in x.collections[:]:
                try:
                    collection.remove()
                except ValueError:
                    pass
            for container in x.containers[:]:
                for artist in list(container):
                    if isinstance(artist, tuple):
                        for item in artist:
                            try:
                                item.remove()
                            except ValueError:
                                pass
                    else:
                        try:
                            artist.remove()
                        except ValueError:
                            pass
        legend = self.ax[0].get_legend()
        maxy = -inf
        miny = inf
        if legend is not None:
            legend.remove()
        for data in dataset['errorbar']:
            errorbar_plot = self.ax[0].errorbar(data['x'], data['y'], data['yerr'], label=data['label'],color=data['color'],fmt='x',alpha=0.8)
            self.errorbarlines.append(errorbar_plot)
        for data in dataset['ax0fill']:
            self.ax[0].fill_between(data['x'], data['y0'], data['y1'], label=data['label'],color=data['color'],alpha=0.6,lw=0)
        for data in dataset['ax1fill']:
            if max(data['y1'])>maxy:
                maxy = max(data['y1'])
            if min(data['y0'])<miny:
                miny = min(data['y0'])
            self.ax[1].fill_between(data['x'], data['y0'], data['y1'], label=data['label'],color=data['color'],alpha=0.6,lw=0)
        for data in dataset['axvline']:
            vline = self.ax[1].axvline(data['x'], ymax=data['ymax'], label=data['label'],color=data['color'])
            self.vlines.append(vline)
        self.ax[0].legend(frameon=False)
        self.minx = dataset['minx']
        self.maxx = dataset['maxx']
        self.miny = dataset['miny']
        self.maxy = dataset['maxy']
        try:
            self.ax[1].set_xlim(left=self.minx, right=self.maxx)
        except:
            pass
        try:
            self.ax[0].set_ylim(bottom=self.miny, top=self.maxy)
        except:
            pass
        try:
            self.ax[1].set_ylim(bottom=0, top=maxy)
        except:
            pass
        overlap = 0.75
        ylim = self.ax[0].get_ylim()
        dy = ylim[1] - ylim[0]
        self.ax[0].set_ylim(bottom=ylim[0] - dy * overlap, top=ylim[1])
        ylim = self.ax[1].get_ylim()
        dy = ylim[1] - ylim[0]
        self.ax[1].set_ylim(bottom=ylim[0], top=ylim[1] + dy * overlap)
        dy = ylim[1] + dy * overlap
        for data in dataset['lines']:
            self.ax[1].plot(data['x'], -0.01*dy-0.02*data['y']*dy, label=data['label'], color=data['color'],lw=5, alpha=0.4)
        self.ax[1].set_ylim(bottom=-0.05*dy)
        ageplot = self.ageBox.isChecked()
        if ageplot:
            self.ax[0].set_ylabel('$^{14}$C age in years')
        else:
            self.ax[0].set_ylabel('F$^{14}$C')
        self.canvas.draw_idle()

        self.threads = [t for t in self.threads if t.isRunning()]
        if len(self.threads)==0:
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)
        self.recalcFlag = False
        self.recalcIndex = None

        for dataset in self.datasets:
            dataset.update_all()

    def setBounds(self,overlap):
        ax = self.ax
        n = len(ax)
        xlim = ax[0].get_xlim()
        xticks = ax[0].get_xticks()

        for i, x in enumerate(ax):
            ticks = x.get_yticks()
            dticks = ticks[1] - ticks[0]
            maxy = max(ticks)
            miny = min(ticks)
            dy = maxy - miny
            nonscaletotheight = n * dy
            totheight = nonscaletotheight - (n - 1) * overlap * dy
            top = maxy + i * (1 - overlap) * dy
            bottom = top - totheight
            ylabelheight = (miny - bottom + dy / 2) / totheight
            labelheight = (miny + 0.8 * dy - bottom) / totheight
            if i % 2 == 0:
                x.yaxis.tick_left()
                x.spines['left'].set_bounds((ticks[1], ticks[-2]))
                x.spines['right'].set_visible(False)
                Axis.set_label_coords(x.yaxis, 1.07, ylabelheight)
            else:
                x.yaxis.tick_right()
                x.spines['right'].set_bounds((ticks[1], ticks[-2]))
                x.spines['left'].set_visible(False)
                Axis.set_label_coords(x.yaxis, 1 + 0.05, ylabelheight)
            x.set_ylim(top=top, bottom=bottom)
            x.set_yticks(ticks[1:-1])
            # x.set_ylabel('')
            x.spines['top'].set_visible(False)
            if i == 0:
                x.spines['bottom'].set_bounds((xticks[1], xticks[-2]))
            else:
                x.spines['bottom'].set_visible(False)


    def redraw(self):
        self.tabindex = self.tabWidget.currentIndex()
        if self.tabindex != -1:
            table = self.datasets[self.tabindex].tableView
            table.resizeColumnsToContents()
            model = table.model()
            model.layoutAboutToBeChanged.emit()
        #self.selectedIndexes = table.selectionModel().selectedIndexes()
        ageplot = self.ageBox.isChecked()
        plotworker = MainPLotWorker(self.datasets,self.curveManager,self.curveColors,recalculate=self.recalcFlag,recalcindex=self.recalcIndex,ageplot=ageplot)
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)
        self.threads.append(plotworker)
        plotworker.finished.connect(self.figure_updated)
        plotworker.start()

    def saveData(self):
        start_folder = 'Library\\SaveFolder'
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            "untitled.txt",  # default file name
            "Text Files (*.xlsx);;All Files (*)",
        )
        if file_path:
            excelWorker = ExcelWorker(self.datasets,self.curveManager,file_path)
            self.progressBar.setVisible(True)
            self.progressBar.setRange(0, 0)
            self.threads.append(excelWorker)
            excelWorker.finished.connect(self.filesSaved)
            excelWorker.start()

    def filesSaved(self):
        self.threads = [t for t in self.threads if t.isRunning()]
        if len(self.threads)==0:
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)

    def load_settings(self):
        height = self.settings['windowheight']
        width = self.settings['windowwidth']
        self.initialize_plot()
        self.resize(width, height)
        posx = self.settings['posx']
        posy = self.settings['posy']
        self.ageBox.setChecked(self.settings['ageBool'])
        self.move(posx, posy)
        self.curveColors = self.settings['curveColors']
        self.curveManager.curves = self.settings['curves']
        folder_path   = self.starfolder + 'DataSettings'
        pkl_files = [f for f in os.listdir(folder_path) if f.endswith(".pkl")]
        self.datasets = []
        if len(pkl_files) > 0:
            for i,file in enumerate(pkl_files):
                self.datasets.append(DataSetManager(self,i,loadData=True))


    def closeEvent(self, event):
        w = self.width()
        h = self.height()
        self.settings = read_settings('display_settings')
        self.settings['windowheight'] = h
        self.settings['windowwidth'] = w
        pos = self.pos()
        self.settings['posx'] = pos.x()
        self.settings['posy'] = pos.y()
        curves = []
        for i in range(self.Ncurves):
            curves.append(self.__dict__[f'curveBox{i}'].currentText())
        self.settings['curves'] = curves
        self.settings['curveColors'] = self.curveColors
        self.settings['ageBool'] = self.ageBox.isChecked()
        folder_path = self.starfolder+'DataSettings'
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):  # Ensure it's a file, not a folder
                os.remove(file_path)
        for data in self.datasets:
            data.saveData()
        write_settings(self.settings, 'display_settings')
        super().closeEvent(event)

    def load_Oxcal_curve(self):
        start_folder = 'Library\\Data\\OxCal'
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", start_folder, "All Files (*);;Oxcal files (*.14c)")
        label = Path(file_path).stem
        if file_path:
            filebool = self.curveManager.load_Oxcal_file(file_path)
            if filebool:
                for dataset in self.datasets:
                    dataset.calc.curveData = self.curveManager
                    dataset.calc.curves = self.curveManager.curves
                    dataset.calc.recalc_all()
                for i in range(self.Ncurves):
                    self.__dict__[f'curveBox{i}'].addItem(label)
                index = self.curveBox0.findText(label)
                if index != -1:  # -1 means not found
                    self.curveBox0.setCurrentIndex(index)


