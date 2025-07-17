import time

from matplotlib import pyplot as plt
from numpy import log, where, array
from numpy import ones, arange,zeros,nanargmax,diff,split, inf
from matplotlib.figure import Figure
from PyQt5.QtCore import QThread, pyqtSignal
import matplotlib
import xlsxwriter
matplotlib.use("Qt5Agg")


class ExcelWorker(QThread):
    finished = pyqtSignal()
    def __init__(self,datasets,curveManager,savefile):
        super().__init__()
        self.datasets = datasets
        self.curveManager = curveManager
        self.curves = self.curveManager.curves
        self.calcs = []
        self.savefile = savefile
        self.data = {'Curves':{}}


    def run(self):
        for dataset in self.datasets:
            calc = dataset.calc
            self.calcs.append(calc)
        self.getData()
        self.savedata()

    def getData(self):
        for i,calc in enumerate(self.calcs):
            self.data[f'{i} {calc.dataName}'] = {}
            for j,curve in enumerate(self.curves):
                if curve is None:
                     continue

                self.getCalcdata(calc, i,curve)
        for i, curve in enumerate(self.curves):
            if curve is None:
                continue

            self.getCurveData(curve)

    def getCurveData(self, curve):
        data = self.curveManager.data[curve]
        x = data['calendaryear']
        y = data['fm']
        dy = data['fm_sig']
        self.data['Curves'][f'{curve} years'] = data['calendaryear']
        self.data['Curves'][f'{curve} fm'] = data['fm']
        self.data['Curves'][f'{curve} fm_sig'] = data['fm_sig']
        age = -8033*log(y)
        age_sig = 8033/data['fm']*dy
        self.data['Curves'][f'{curve} age'] = age
        self.data['Curves'][f'{curve} age_sig'] = age_sig


    def getCalcdata(self, calc, index,curve):
        curve = self.curves[index]
        try:
            maxind = nanargmax(calc.data[curve]['probability'])
        except ValueError:
            maxind = None
        if maxind is not None and len(calc.wiggleyears)>0:
            maxyear = calc.data[curve]['tyears'][maxind]
            x = calc.wiggleyears + maxyear - max(calc.wiggleyears)
            y = calc.wigglefms
            dy = calc.wigglefms_sig
            self.data[f'{index} {calc.dataName}'][f'Best match years\n{curve}'] = x
            self.data[f'{index} {calc.dataName}']['fm'] = y
            self.data[f'{index} {calc.dataName}']['fm_sig'] = dy
            y = -8033 * log(y)
            dy = 8033 / calc.wigglefms * dy
            self.data[f'{index} {calc.dataName}']['age'] = y
            self.data[f'{index} {calc.dataName}']['age_sig'] = dy
            self.data[f'{index} {calc.dataName}'][f'test years\n{curve}'] = calc.data[curve]['tyears']+calc.shift
            self.data[f'{index} {calc.dataName}'][f'Probability density\n{curve}'] = calc.data[curve]['probability']

    def savedata(self):
        with xlsxwriter.Workbook(self.savefile) as workbook:
            def number_to_letters(n):
                result = ''
                while n > 0:
                    n -= 1
                    result = chr(n % 26 + 65) + result
                    n //= 26
                return result
            for sheetkey in self.data.keys():
                worksheet = workbook.add_worksheet(sheetkey)
                data = self.data[sheetkey]
                for i, key in enumerate(data.keys()):
                    worksheet.write(0, i, key)
                    for j, val in enumerate(data[key]):
                        try:
                            worksheet.write(j + 1, i, val)
                        except:
                            continue
        self.finished.emit()

