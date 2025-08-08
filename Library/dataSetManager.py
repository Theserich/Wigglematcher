from Library.dataMager import Calculator,default_plot_settings,default_offset_settings
from Library.tableModel import MyTableModel
from PyQt5.QtWidgets import QTableView, QPushButton, QLineEdit, QWidget, QColorDialog, QGridLayout, QCheckBox,QRadioButton,QButtonGroup
from PyQt5.QtGui import QPalette
from Library.comset import *
import pickle
from copy import copy
from PyQt5.uic import loadUi
from Library.PLotWindow import PlotWindow_test
from matplotlib import pyplot as plt
from Library.PlotWorker import PLotWorker,PlotWindow
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import QTimer
from pathlib import Path


class DataSetManager(QWidget):
    def __init__(self,widget,index,loadData=False):
        super().__init__()
        self.folder = Path('Library/Settings/DataSettings/')
        self.widgetFile = Path('Library/UIFiles/DatasetWidget.ui')
        self.tabIndex = index
        self.widget = widget
        self.loadData(loadData)
        self.tabWidget = self.widget.tabWidget
        loadUi(self.widgetFile, self)
        self.setup_offsets()
        self.tableModel = MyTableModel(self.calc, parent=self.widget,index=self.tabIndex)
        self.tableView.setModel(self.tableModel)

        self.tableView.setSortingEnabled(True)
        self.plotCheckBox.setChecked(self.calc.plotsettings['plotbool'])
        for i, (color, check,show) in enumerate(zip(self.calc.plotsettings['colors'],self.calc.plotsettings['colorbools'],self.calc.plotsettings['showfits'])):
            self.__dict__[f'colorCheck{i}'].setChecked(check)
            self.__dict__[f'colorCheck{i}'].clicked.connect(self.check_color)
            self.__dict__[f'showCheck{i}'].setChecked(show)
            self.__dict__[f'showCheck{i}'].clicked.connect(self.check_plot)
            self.__dict__[f'colorButton{i}'].setStyleSheet(f"background-color: {self.calc.plotsettings['buttonColors'][i]};")
            self.__dict__[f'colorButton{i}'].clicked.connect(self.open_color_dialog)
        self.ChronoCheck.setChecked(self.calc.plotsettings['chronology'])
        self.ChronoCheck.clicked.connect(self.showChronology)
        self.plotCheckBox.clicked.connect(self.checkDataPLot)
        self.deleteButton.clicked.connect(self.remove_dataset)

        self.loadButton.clicked.connect(lambda: self.calc.load_data(self))
        self.addButton.clicked.connect(self.tableModel.addDate)
        self.tableView.clicked.connect(self.tableModel.tableClicked)
        self.tabWidget.addTab(self, self.calc.plotsettings['dataName'])
        self.buttonDict = {'consitencyPLotButton': {'progressbar': 'progressBar', 'index': 0},
                           'individualPLotButton':{'progressbar': 'progressBar2', 'index': 0},
                           'consitencyPLotButton2':{'progressbar': 'progressBar', 'index': 1},
                           'individualPLotButton2':{'progressbar': 'progressBar2', 'index': 1}}
        for button in self.buttonDict:
            self.__dict__[self.buttonDict[button]['progressbar']].setVisible(False)
            self.__dict__[button].clicked.connect(lambda: self.plotGraph())
        self.changing = False
        self.shiftEdit.valueChanged.connect(self.changeShift)
        self.offsetSlider.valueChanged.connect(self.changeOffset)
        self.offset.valueChanged.connect(self.changeOffset)
        self.set_Agreement_and_OffsetLabels()
        self.tableView.resizeColumnsToContents()
        self.plotWorkers = []
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.widget.redraw)

    def set_offsetValues(self):
        if self.changing == True:
            return
        premanual = self.calc.offset_settings['Manual']
        for key in ['min','max','step','offset','offset_sig','mu','sigma']:
            self.calc.offset_settings[key] = self.__dict__[key].value()
        if self.AutoOffset.isChecked():
            self.calc.offset_settings['Manual'] = False
            if premanual == False:
                return
        else:
            self.calc.offset_settings['Manual'] = True
            if premanual == True:
                return
        if self.GaussianPrior.isChecked():
            self.calc.offset_settings['GaussianPrior'] = True
        else:
            self.calc.offset_settings['GaussianPrior'] = False
        self.activate_offset_fields()
        self.widget.recalcFlag = True
        self.widget.recalcIndex = self.tabIndex
        self.debounce_timer.start(100)
        self.changing = False

    def activate_offset_fields(self):
        if self.calc.offset_settings['Manual']:
            for key in ['offsetSlider', 'offset', 'offset_sig']:
                self.__dict__[key].setEnabled(True)
            for key in ['min', 'max', 'step', 'mu', 'sigma', 'UniformPrior', 'GaussianPrior']:
                self.__dict__[key].setEnabled(False)
        else:
            for key in ['offsetSlider', 'offset', 'offset_sig']:
                self.__dict__[key].setEnabled(False)
            for key in ['min', 'max', 'step', 'mu', 'sigma', 'UniformPrior', 'GaussianPrior']:
                self.__dict__[key].setEnabled(True)

    def setup_offsets(self):
        for key in ['min','max','step','offset','offset_sig','mu','sigma']:
            self.__dict__[key].setValue(self.calc.offset_settings[key])
            self.__dict__[key].valueChanged.connect(self.set_offsetValues)
            self.AutoOffset.setChecked(True)
        if self.calc.offset_settings['GaussianPrior']:
            self.GaussianPrior.setChecked(True)
        else:
            self.UniformPrior.setChecked(True)
        self.activate_offset_fields()
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)  # This is actually the default
        self.button_group.addButton(self.ManualOffset)
        self.button_group.addButton(self.AutoOffset)
        if self.calc.offset_settings['Manual']:
            self.ManualOffset.setChecked(True)
        else:
            self.AutoOffset.setChecked(True)
        for key in ['UniformPrior', 'GaussianPrior', 'AutoOffset', 'ManualOffset']:
            self.__dict__[key].clicked.connect(self.set_offsetValues)
        self.offsetSlider.setValue(int(self.calc.offset))

    def changeOffset(self,value):
        widget = self.sender()
        name = widget.objectName()
        if self.changing == False:
            self.changing = True
            if name == 'offsetSlider':
                self.offset.setValue(value)
            elif name == 'offset':
                self.offsetSlider.setValue(int(value))
            self.calc.offset = value
            self.calc.offset_settings['offset'] = value
            self.widget.recalcFlag = True
            self.widget.recalcIndex = self.tabIndex
            self.widget.redraw()
        self.changing = False

    def changeShift(self,value):
        widget = self.sender()
        self.calc.shift = value
        self.widget.redraw()

    def changeOffsetSig(self,value):
        self.calc.offset_sig = value
        self.widget.recalcFlag = True
        self.widget.recalcIndex = self.tabIndex
        self.widget.redraw()
        self.changing = False

    def update_all(self):
        self.set_Agreement_and_OffsetLabels()
        self.tableModel.updateHeader()
        self.tableModel.layoutChanged.emit()

    def showChronology(self):
        self.calc.plotsettings['chronology'] = self.ChronoCheck.isChecked()
        self.widget.redraw()

    def plotGraph(self):
        widget = self.sender()
        button = widget.objectName()
        progressbar = self.__dict__[self.buttonDict[button]['progressbar']]
        calc = self.calc
        index = self.buttonDict[button]['index']
        if calc.curves[index] is not None:
            widget.setEnabled(False)
            self.__dict__[button].setVisible(True)
            progressbar.setVisible(True)
            plotworker = PLotWorker(calc,plotButton=button,curveind=index)
            self.plotWorkers.append(plotworker)
            plotworker.progress.connect(self.update_progress)
            plotworker.finished.connect(self.display_plot)
            plotworker.start()

    def plotGraph_experimental(self):
        widget = self.sender()
        button = widget.objectName()
        #widget.setEnabled(False)
        progressbar = self.__dict__[self.buttonDict[button]['progressbar']]
        index = self.buttonDict[button]['index']
        plotwindow = PlotWindow_test(self.calc,curveind=index,plotButton=button)

    def set_Agreement_and_OffsetLabels(self):
        for i,curve in enumerate(self.calc.curves):
            if curve is not None:
                try:
                    agreement = self.calc.data[curve]['A']*100
                    threshold = self.calc.data[curve]['A_n']*100
                    self.__dict__[f'agreementLabel{i}'].setText(f'{curve}: {agreement:.2f}%')
                    self.threshLabel.setText(f'threshold: {threshold:.2f}%')
                    if self.calc.offset_settings['Manual']:
                        self.__dict__[f'offsetLabel{i}'].setText('')
                    else:
                        self.__dict__[f'offsetLabel{i}'].setText(
                            f'{curve}: {self.calc.data[curve]["offset"]:.1f} ± {self.calc.data[curve]["offset_sig"]:.1f}')
                except:
                    self.__dict__[f'agreementLabel{i}'].setText('')
                    self.__dict__[f'offsetLabel{i}'].setText('')
            else:
                self.__dict__[f'offsetLabel{i}'].setText('')
                self.__dict__[f'agreementLabel{i}'].setText('')

    def display_plot(self, data):
        (fig,name) = data
        plot_window = PlotWindow(fig, name)
        plot_window.show()
        plot_window.raise_()
        setattr(self, f'plot_window_{id(plot_window)}', plot_window)
        self.__dict__[self.buttonDict[name]['progressbar']].setVisible(False)
        self.__dict__[name].setEnabled(True)
        self.plotWorkers = [t for t in self.plotWorkers if t.isRunning()]



    def update_progress(self, values):
        [value,button] = values
        self.__dict__[self.buttonDict[button]['progressbar']].setValue(value)


    def checkDataPLot(self):
        self.calc.plotsettings['plotbool'] = self.plotCheckBox.isChecked()
        self.widget.redraw()

    def saveData(self):
        file_path = Path(self.folder) / f"{self.tabIndex}.pkl"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('wb') as file:
            pickle.dump(self.calc, file)


    def loadData(self,loadData):
        if loadData == False:
            self.calc = Calculator(self.widget.curveManager)
            self.calc.dataName = f'Tab {self.tabIndex}'
            self.calc.plotsettings['colors'] = copy(self.widget.curveColors)
            self.buttonColors = self.calc.plotsettings['buttonColors']
        else:
            pkl_path = Path(self.folder) / f"{self.tabIndex}.pkl"
            try:
                self.calc = pickle.load(open(pkl_path, 'rb'))
                if 'plotsettings' not in self.calc.__dict__:
                    self.calc.plotsettings = default_plot_settings
                else:
                    for key in default_plot_settings:
                        if key not in self.calc.plotsettings:
                            self.calc.plotsettings[key] = default_plot_settings[key]
                if 'offset_settings' not in self.calc.__dict__:
                    self.calc.offset_settings = default_offset_settings
                else:
                    for key in default_offset_settings:
                        if key not in self.calc.offset_settings:
                            self.calc.offset_settings[key] = default_offset_settings[key]
            except Exception as e:
                self.calc = Calculator(self.widget.curveManager)
                self.calc.dataName = f'Tab {self.tabIndex}'
                self.calc.plotsettings['colors'] = copy(self.widget.curveColors)
                self.buttonColors = self.calc.plotsettings['buttonColors']

    def check_color(self):
        widget = self.sender()
        name = widget.objectName()
        index = int(name[-1])
        precolor = self.calc.plotsettings['colors'] [index]
        self.calc.plotsettings['colorbools'][index] = widget.isChecked()
        if widget.isChecked():
            button = self.__dict__[f'colorButton{index}']
            color = button.palette().color(QPalette.Button)
            self.calc.plotsettings['colors'][index] = color.name()
        else:
            self.calc.plotsettings['colors'][index] = self.widget.curveColors[index]
        if precolor != self.calc.plotsettings['colors'][index]:
            self.widget.redraw()

    def check_plot(self):
        widget = self.sender()
        name = widget.objectName()
        index = int(name[-1])
        self.calc.plotsettings['showfits'][index] = widget.isChecked()
        self.widget.redraw()

    def remove_dataset(self):
        self.widget.tabWidget.removeTab(self.widget.tabWidget.indexOf(self))
        del self.widget.datasets[self.tabIndex]
        for i, dataset in enumerate(self.widget.datasets):
            dataset.tabIndex = i
        self.widget.redraw()

    def open_color_dialog(self):
        widget = self.sender()
        button = widget.objectName()
        color = QColorDialog.getColor()
        index = int(button[-1])
        if color.isValid():
            colname = color.name()
            if self.__dict__[f'colorCheck{index}'].isChecked():
                self.calc.plotsettings['colors'][index] = colname
                self.widget.redraw()
            self.calc.plotsettings['buttonColors'][index] = colname
            widget.setStyleSheet(f"background-color: {colname};")