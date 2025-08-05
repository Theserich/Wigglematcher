from Library.dataMager import Calculator,default_plot_settings,default_offset_settings
from Library.tableModel import MyTableModel
from PyQt5.QtWidgets import QTableView, QPushButton, QLineEdit, QWidget, QColorDialog, QGridLayout, QCheckBox
from PyQt5.QtGui import QPalette
from Library.comset import *
import pickle
from copy import copy
from PyQt5.uic import loadUi
from Library.PLotWindow import PlotWindow_test
from matplotlib import pyplot as plt
from Library.PlotWorker import PLotWorker,PlotWindow
from PyQt5.QtCore import QThread, pyqtSignal


class DataSetManager(QWidget):
    def __init__(self,widget,index,loadData=False):
        super().__init__()
        self.folder = 'Library\\Settings\\DataSettings\\'
        self.widgetFile = 'Library\\UIFiles\\DatasetWidget.ui'
        self.tabIndex = index
        self.widget = widget
        if loadData:
            self.loadData()
        else:
            self.calc = Calculator(widget.curveManager)
            self.calc.dataName = f'Tab {index}'
            self.colors = copy(self.widget.curveColors)
            self.calc.plotsettings['colors'] = self.colors
            self.buttonColors = self.calc.plotsettings['buttonColors']

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
            self.__dict__[f'colorButton{i}'].setStyleSheet(f"background-color: {self.buttonColors[i]};")
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
        self.setAgreementLabels()
        self.tableView.resizeColumnsToContents()
        self.plotWorkers = []

    def set_offsetValues(self):
        self.changing = True

        for key in ['min','max','step','offset','offset_sig','mu','sigma']:
            self.calc.offset_settings[key] = self.__dict__[key].value()
        if self.AutoOffset.isChecked():
            self.calc.offset_settings['Manual'] = False
        else:
            self.calc.offset_settings['Manual'] = True
        if self.GaussianPrior.isChecked():
            self.calc.offset_settings['GaussianPrior'] = True
        else:
            self.calc.offset_settings['GaussianPrior'] = False

        self.offsetSlider.setValue(int(self.calc.offset))
        self.changing = False

        self.widget.recalcFlag = True
        self.widget.recalcIndex = self.tabIndex
        self.widget.redraw()

    def setup_offsets(self):
        for key in ['min','max','step','offset','offset_sig','mu','sigma']:
            self.__dict__[key].setValue(self.calc.offset_settings[key])
            self.__dict__[key].valueChanged.connect(self.set_offsetValues)
        if self.calc.offset_settings['Manual']:
            self.ManualOffset.setChecked(True)
        else:
            self.AutoOffset.setChecked(True)
        if self.calc.offset_settings['GaussianPrior']:
            self.GaussianPrior.setChecked(True)
        else:
            self.UniformPrior.setChecked(True)
        self.GaussianPrior.setChecked(True)
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
        self.tableModel.data = self.calc.wiggledata
        self.setAgreementLabels()
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

    def setAgreementLabels(self):
        for i,curve in enumerate(self.calc.curves):
            if curve is not None:
                try:
                    agreement = self.calc.data[curve]['A']*100
                    threshold = self.calc.data[curve]['A_n']*100
                    self.__dict__[f'agreementLabel{i}'].setText(f'{curve}: {agreement:.2f}%')
                    self.threshLabel.setText(f'threshold: {threshold:.2f}%')
                except:
                    self.__dict__[f'agreementLabel{i}'].setText('')
            else:
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
        settings = {}
        for key in ['dataName','colors','colorbools','buttonColors','plotbool','showfits']:
            settings[key] = self.calc.plotsettings[key]
        write_settings(settings, f'DataSettings\\Settings{self.tabIndex}')
        with open(f'{self.folder}{self.tabIndex}.pkl', 'wb') as file:
            pickle.dump(self.calc, file)


    def loadData(self):
        settings = read_settings(f'DataSettings\\Settings{self.tabIndex}')
        try:
            self.calc = pickle.load(open(f'{self.folder}{self.tabIndex}.pkl', 'rb'))
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
            for key in settings:
                self.__dict__[key] = settings[key]
                self.calc.plotsettings[key] = settings[key]
            self.calc.plotsettings['colors'] = self.colors
        except:
            self.calc = Calculator(self.widget.curveManager)
            self.calc.dataName = f'Tab {self.tabIndex}'
            self.colors = copy(self.widget.curveColors)
            self.calc.plotsettings['colors'] = self.colors
            self.buttonColors = self.calc.plotsettings['buttonColors']

    def check_color(self):
        widget = self.sender()
        name = widget.objectName()
        index = int(name[-1])
        precolor = self.colors[index]
        self.calc.plotsettings['colorbools'][index] = widget.isChecked()
        if widget.isChecked():
            button = self.__dict__[f'colorButton{index}']
            color = button.palette().color(QPalette.Button)
            self.calc.plotsettings['colors'][index] = color.name()
        else:
            button = self.widget.__dict__[f'colorbutton{index}']
            color = button.palette().color(QPalette.Button)
            self.colors[index] = color.name()
        if precolor != self.colors[index]:
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
            self.buttonColors[index] = colname
            widget.setStyleSheet(f"background-color: {colname};")