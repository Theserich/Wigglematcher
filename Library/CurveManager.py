import copy

from matplotlib import pyplot as plt

from Library.HelperFunctions import *
from numpy import exp, log, arange, zeros, random, ones, sin, pi, append, all as npall, diff, mean, sum as npsum, sqrt
from PyQt5.QtWidgets import  QFileDialog
from pathlib import Path
import json
from PyQt5.QtWidgets import QMessageBox
from scipy.interpolate import interp1d
from Library.timer import timer

class CurveManager():
    def __init__(self):
        self.curve_folder = 'Library\\Data\\Curves\\'
        self.syntherror = 1.5
        self.amp = 0.8
        self.curves = ['intcal20', 'None']
        self.curve_windows = [1, 1]
        self.load_all_curves()
        #for curve in self.data:
        #    for window_length in range(1,10):
        #        self.generate_averaged_curves(curve,window_length)

    def generate_averaged_curves(self,curve,window_length):
        if f'fm_{window_length}' not in self.data[curve]:
            self.data[curve][f'calendaryear_{window_length}'] = []
            self.data[curve][f'fm_{window_length}'] = []
            self.data[curve][f'fm_sig_{window_length}'] = []
            years = self.data[curve]['calendaryear']
            fms = self.data[curve]['fm']
            fms_sig = self.data[curve][f'fm_sig']
            for i,year in enumerate(years[:-window_length]):
                window_years = years[i:i+window_length]
                window_fms = fms[i:i+window_length]
                window_fms_sig = fms_sig[i:i+window_length]
                if npall(diff(window_years) == 1):
                    weights = 1/window_fms_sig**2
                    fm = npsum(window_fms*weights)/npsum(weights)
                    fm_sig = sqrt(1/npsum(weights))
                    self.data[curve][f'calendaryear_{window_length}'].append(year)
                    self.data[curve][f'fm_{window_length}'].append(fm)
                    self.data[curve][f'fm_sig_{window_length}'].append(fm_sig)
                else:
                    self.data[curve][f'calendaryear_{window_length}'].append(window_years[0])
                    self.data[curve][f'fm_{window_length}'].append(window_fms[0])
                    self.data[curve][f'fm_sig_{window_length}'].append(window_fms_sig[0])
            self.data[curve][f'calendaryear_{window_length}'] = array(self.data[curve][f'calendaryear_{window_length}'])
            self.data[curve][f'fm_{window_length}'] = array(self.data[curve][f'fm_{window_length}'])
            self.data[curve][f'fm_sig_{window_length}'] = array(self.data[curve][f'fm_sig_{window_length}'])
            self.save_curve(curve)


    def load_all_curves(self):
        folder = 'Library\\Data\\Curves\\'
        files = list(Path(folder).glob('*.json'))
        self.data = {}
        for file in files:
            file_name = file.stem
            with open(file, 'rb') as dat:
                data = json.load(dat)
            for key in data:
                data[key] = array(data[key])
            self.data[file_name] = data


    def save_curves(self):
        folder = 'Library\\Data\\Curves\\'
        for curve in self.data:
            data = self.data[key]
            savedata = {}
            for key in data:
                savedata[key] = list(data[key])
            with open(f'{folder}{curve}.json', 'wb') as file:
                json.dump(data, file)

    def save_curve(self,curve):
        folder = 'Library\\Data\\Curves\\'
        data = self.data[curve]
        savedata = {}
        for key in data:
            savedata[key] = list(data[key])
        with open(f'{folder}{curve}.json', 'w', encoding='utf-8') as file:
            json.dump(savedata, file)

    def load_Oxcal_file(self,file_path):
        savename = Path(file_path).stem
        result_dict = {}
        headers = ['bp', '14C age', 'Sigma1', 'Delta 14C', 'Sigma']
        with open(file_path, 'r') as file:
            N = sum(1 for line in file if not line.lstrip().startswith('#'))
        with open(file_path, 'r') as file:
            startbool = True
            secondheader = False
            lines = file.readlines()
            for head in headers:
                result_dict[head] = zeros(N)
            j = 0
            for line in lines:
                if line.lstrip().startswith('#') and startbool:
                    continue
                elif line.lstrip().startswith('#'):
                    secondheader = True
                    continue
                startbool = False
                line = line.replace('!', '').replace('?', '')
                if secondheader == False:
                    values = line.strip().split(',')
                    for i in range(len(headers)):
                        value = values[i]
                        clean_value = value.split('#')[0].strip()  # Removes comment and extra whitespace
                        number = float(clean_value)
                        result_dict[headers[i]][j] = number
                else:
                    values = line.strip().split('\t')
                    result_dict['bp'][j] = 1950-float(values[0])
                    result_dict['14C age'][j] = -8033*log(float(values[3]))
                    result_dict['Sigma1'][j] = 8033/float(values[3])*float(values[4])
                j += 1
        newdict = {}
        newdict['calendaryear'] = 1950-result_dict['bp']
        newdict['bp'] = result_dict['bp']
        newdict['fm'] = exp(-result_dict['14C age']/8033)
        newdict['fm_sig'] = newdict['fm'] /8033*result_dict['Sigma1']
        savedict = {}
        for key in newdict:
            savedict[key] = list(newdict[key])
        self.data[savename] = newdict
        for window_length in range(1, 2):
            self.generate_averaged_curves(savename,window_length)
        with open(f'{self.curve_folder}{savename}.json', 'w', encoding='utf-8') as file:
            json.dump(savedict, file)
        return True

    def load_excel_curve(self, widget):
        start_folder = 'Library\\Data\\ExcelCurves'
        file_path, _ = QFileDialog.getOpenFileName(widget, "Open File", start_folder,
                                                   "All Files (*);;Excel files(*.xlsx)")
        label = Path(file_path).stem
        if file_path:
            print(f"Selected file: {file_path}")
        else:
            return
        df = loadexcel(file_path)
        datakeys = list(df.keys())
        newdata = {}
        if 'age' in datakeys and 'age_sig' in datakeys:
            newdata['fm'] = exp(-df['age'] / 8033)
            newdata['fm_sig'] = newdata['fm'] / 8033 * df['age_sig']
        elif 'fm' in datakeys and 'fm_sig' in datakeys:
            newdata['fm'] = df['fm']
            newdata['fm_sig'] = df['fm_sig']
        else:
            QMessageBox.warning(None, "Invalid headers in the file",
                                "Header most include 'age' and 'age_sig' or 'fm' and 'fm_sig'.")
            return
        if 'year' in datakeys:
            newdata['bp'] = 1950 - df['year']
        elif 'bp' in datakeys:
            newdata['bp'] = df['bp']
        elif 'calendaryear' in datakeys:
            newdata['bp'] = 1950-df['calendaryear']
        else:
            QMessageBox.warning(None, "Invalid headers in the file",
                                "Please add a header with 'bp', 'year' or 'calendaryear'")
            return
        fill_curve = 'intcal20'
        fill_data = self.data[fill_curve]
        newdata['bp'] = append(newdata['bp'], fill_data['bp'][0])
        newdata['bp'] = append(newdata['bp'], fill_data['bp'][-1])
        newdata['fm'] = append(newdata['fm'], fill_data['fm'][0])
        newdata['fm'] = append(newdata['fm'], fill_data['fm'][-1])
        newdata['fm_sig'] = append(newdata['fm_sig'], fill_data['fm_sig'][0])
        newdata['fm_sig'] = append(newdata['fm_sig'], fill_data['fm_sig'][-1])
        sortdf(newdata, 'bp')
        for i, bp in enumerate(newdata['bp'][1:]):
            bp = float(bp)
            bp0 = float(newdata['bp'][i])
            if bp - bp0 > 10:
                intcalindexes = where((fill_data['bp'] > bp0) & (fill_data['bp'] < bp))[0]
                for k in ['fm', 'fm_sig', 'bp']:
                    newdata[k] = append(newdata[k], fill_data[k][intcalindexes])
        [fms, fmsigs, years] = getF14CfromDataframe(newdata)
        newdata = {}
        newdata['calendaryear'] = years
        newdata['bp'] = 1950 - years
        newdata['fm'] = fms
        newdata['fm_sig'] = fmsigs
        savedata = {}
        for key in newdata:
            savedata[key] = list(newdata[key])
        self.data[label] = newdata
        for dataset in widget.datasets:
            dataset.calc.curveData = self
        widget.recalcFlag = True

        with open(f'{self.curve_folder}{label}.json', 'w') as file:
            json.dump(savedata, file)
        for i in range(widget.Ncurves):
            widget.__dict__[f'curveBox{i}'].addItem(label)
        index = widget.curveBox0.findText(label)
        if index != -1:  # -1 means not found
            widget.curveBox0.setCurrentIndex(index)
        widget.redraw()