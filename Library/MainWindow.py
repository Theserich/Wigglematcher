from PyQt5.uic import loadUi
from pathlib import Path
import os

from Library.comset import read_settings, write_settings
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QFileDialog, QColorDialog,QMessageBox
from PyQt5.Qt import Qt
from Library.dataSetManager import DataSetManager
from Library.PlotManager import PlotManager
from Library.timer import timer
from numpy import where, zeros, argmax,append, log, exp, arange,diff,ones,split, inf
from Library.CurveManager import CurveManager
from Library.MainPlotThread import MainPLotWorker
import matplotlib
from Library.ExcelWorker import ExcelWorker
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.Qt import Qt
from numpy import log, where, zeros, arange, diff, split, inf, nanargmax
matplotlib.use("Qt5Agg")


class WidgetMain(QMainWindow):
    def __init__(self, path):
        self.plotFms = False
        self.starfolder = Path('Library\\Settings\\')
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
            curvestring = curve
            if curve is None:
                curvestring = 'None'
            index = self.__dict__[f'curveBox{i}'].findText(curvestring)
            if index != -1:  # -1 means not found
                self.__dict__[f'curveBox{i}'].setCurrentIndex(index)
        self.ageBox.stateChanged.connect(self.changeToAge)
        self.addDatasetButton.clicked.connect(self.addDataset_tab)
        self.actionLoad_in_Curve.triggered.connect(self.load_Oxcal_curve)
        self.actionLoad_in_curve_from_xlsx.triggered.connect(lambda: self.curveManager.load_excel_curve(self))
        self.actionSave_results_to_xlsx.triggered.connect(self.saveData)
        for i in range(self.Ncurves):
            self.__dict__[f'curveBox{i}'].currentIndexChanged.connect(self.changeCurves)
        self.recalcFlag = False
        self.recalcIndex = None
        self.threads = []
        self.plotworker_cleanup_in_progress = False
        self.plot_manager = PlotManager(self.widget, self.curveManager)
        self.redraw()
        self.adjust_scrollarea_width()

    def safely_start_worker(self):
        if self.plotworker_cleanup_in_progress:
            return  # Prevent overlapping cleanup
        if hasattr(self, 'plotworker') and self.plotworker is not None:
            if self.plotworker.isRunning():
                self.plotworker_cleanup_in_progress = True
                self.plotworker.finished.connect(self._on_plotworker_cleanup_done)
                self.plotworker.quit()
                self.plotworker.wait()
                return
        self._start_worker_internal()

    def _on_plotworker_cleanup_done(self):
        self.plotworker.finished.disconnect(self._on_plotworker_cleanup_done)
        self.plotworker.finished.disconnect(self.plot_manager.plot_datasets)
        self.plotworker.finished.disconnect(self.update_widgets)
        self.plotworker.finishedBool.disconnect(self.cleanup)

        self.plotworker_cleanup_in_progress = False
        self._start_worker_internal()

    def _start_worker_internal(self):
        self.plotworker = MainPLotWorker(self.datasets,self.curveManager,self.curveColors,recalculate=self.recalcFlag,recalcindex=self.recalcIndex,ageplot=self.ageplot)
        self.plotworker.finished.connect(self.plot_manager.plot_datasets)
        self.plotworker.finished.connect(self.update_widgets)
        self.plotworker.finishedBool.connect(self.cleanup)
        self.plotworker.start()

    def cleanup(self):
        self.threads = [t for t in self.threads if t.isRunning()]
        if len(self.threads) == 0:
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)
        self.recalcFlag = False
        self.recalcIndex = None

    @timer
    def redraw(self):
        self.tabindex = self.tabWidget.currentIndex()
        if self.tabindex != -1:
            table = self.datasets[self.tabindex].tableView
            table.resizeColumnsToContents()
            model = table.model()
            model.layoutAboutToBeChanged.emit()
        self.ageplot = self.ageBox.isChecked()
        self.safely_start_worker()
        self.progressBar.setVisible(True)
        self.progressBar.setRange(0, 0)
        self.threads.append(self.plotworker)
        self.plotworker.start()

    def update_widgets(self):
        for dataset in self.datasets:
            dataset.update_all()


    def changeCurves(self):
        for i in range(self.Ncurves):
            curve = self.__dict__[f'curveBox{i}'].currentText()
            if curve == 'None':
                curve = None
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
                if curve is not None:
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


    def changeToAge(self):
        for dataset in self.datasets:
            dataset.tableModel.updateHeader()
        self.redraw()


    def saveData(self):
        start_folder = 'Library\\SaveFolder'
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            "untitled.xlsx",  # default file name
            "Excel Files (*.xlsx);;All Files (*)",
        )
        if file_path:
            excelWorker = ExcelWorker(self.datasets,self.curveManager,file_path)
            excelWorker.finished.connect(self.filesSaved)
            excelWorker.error_occurred.connect(self.show_error_message)
            self.threads.append(excelWorker)
            excelWorker.start()

    def show_error_message(self, error_message):
        """Display error message when Excel export fails"""
        # Clean up progress bar
        self.threads = [t for t in self.threads if t.isRunning()]
        if len(self.threads) == 0:
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)

        # Show error dialog
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Excel Export Error")
        msg_box.setText("Failed to export data to Excel file")
        msg_box.setDetailedText(error_message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def filesSaved(self):
        self.threads = [t for t in self.threads if t.isRunning()]
        if len(self.threads)==0:
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(0)

    def load_settings(self):
        defaultSettings = {'windowheight':1000,'windowwidth':1600,'ageBool':True,'posx':0,'posy':0,'curves':['None','None'],'curveColors':['#ff5500','#000000']}
        self.settings = read_settings('display_settings')
        if self.settings is not None:
            for key in defaultSettings:
                if key not in self.settings:
                    self.settings[key] = defaultSettings[key]
        else:
            self.settings = defaultSettings
        height = self.settings['windowheight']
        width = self.settings['windowwidth']
        self.resize(width, height)
        posx = self.settings['posx']
        posy = self.settings['posy']
        self.move(posx, posy)
        self.ageBox.setChecked(self.settings['ageBool'])
        self.curveColors = self.settings['curveColors']
        self.curveManager.curves = self.settings['curves']
        for i,curve in enumerate(self.curveManager.curves):
            if curve == 'None':
                self.curveManager.curves[i] = None
        folder_path   = self.starfolder / 'DataSettings'
        os.makedirs(folder_path, exist_ok=True)
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
        folder_path = self.starfolder/'DataSettings'
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

    def adjust_scrollarea_width(self):
        """Adjust the scroll area width to fit table content without horizontal scrollbar"""
        # Get the table view
        curentTabIndex = self.tabWidget.currentIndex()
        if curentTabIndex == -1:
            return
        table_view = self.datasets[curentTabIndex].tableView

        table_view.resizeColumnsToContents()
        model = table_view.model()

        total_width = 0
        for column in range(model.columnCount()):
            total_width += table_view.columnWidth(column)

        padding = 70

        if table_view.verticalScrollBar().isVisible():
            total_width += table_view.verticalScrollBar().width()

        required_width = total_width + padding
        self.scrollarea.setFixedWidth(required_width)

        #width2 = self.datasets[curentTabIndex].groupBox_2.width() + padding
        #required_width = max(width2, required_width)
        max_width = 1500
        if required_width > max_width:
            self.scrollarea.setFixedWidth(max_width)
            # Re-enable horizontal scrolling if content is too wide
            table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            # Disable horizontal scrolling since everything fits
            table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

