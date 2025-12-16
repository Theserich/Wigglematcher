import os

from src.HelperFunctions import *
from numpy import exp, log, zeros, append, all as npall, diff, sum as npsum, sqrt
from PyQt5.QtWidgets import  QFileDialog
from pathlib import Path
import json
from PyQt5.QtWidgets import QMessageBox

class CurveManager():
    def __init__(self):
        self.curve_folder = Path('Library/Data/Curves')
        self.curve_folder.mkdir(parents=True, exist_ok=True)
        self.syntherror = 1.5
        self.amp = 0.8
        self.curves = ['intcal20', None]
        self.curve_windows = [1, 1]
        self.load_all_curves()

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
        folder = Path('Library/Data/Curves')
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
        folder = Path('Library\\Data\\Curves\\')
        for curve in self.data:
            data = self.data[key]
            filename = f'{curve}.json'
            savedata = {}
            for key in data:
                savedata[key] = list(data[key])
            with open(Path(folder /filename), 'wb') as file:
                json.dump(data, file)

    def delete_curve(self,curve):
        folder = Path('Library\\Data\\Curves\\')
        filename = f'{curve}.json'
        file_path = Path(folder /filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    def save_curve(self, curve):
        folder = Path('Library') / 'Data' / 'Curves'
        folder.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

        data = self.data[curve]
        savedata = {key: list(data[key]) for key in data}

        file_path = folder / f'{curve}.json'
        with file_path.open('w', encoding='utf-8') as file:
            json.dump(savedata, file)

    def load_curve(self, widget=None):
        start_folder = 'Library/Data'
        file_path, _ = QFileDialog.getOpenFileName(
            widget,
            "Open File",
            start_folder,
            "All Files (*);;OxCal (*.14c);;Excel (*.xlsx);;CSV (*.csv)"
        )
        if not file_path:
            return
        file_path = Path(file_path)
        label = file_path.stem
        suffix = file_path.suffix.lower()
        if suffix in parse_dict:
            newdata = parse_dict[suffix](file_path)
        else:
            QMessageBox.warning(None, "Unsupported file type",
                                f"Cannot load files of type {suffix}")
            return
        fill_curve = 'intcal20'
        fill_data = self.data[fill_curve]
        for key in ['bp', 'fm', 'fm_sig']:
            newdata[key] = append(newdata[key], fill_data[key][0])
            newdata[key] = append(newdata[key], fill_data[key][-1])
        sortdf(newdata, 'bp')
        for i, bp in enumerate(newdata['bp'][1:]):
            bp0 = float(newdata['bp'][i])
            bp = float(bp)
            if bp - bp0 > 10:
                idx = where((fill_data['bp'] > bp0) & (fill_data['bp'] < bp))[0]
                for k in ['bp', 'fm', 'fm_sig']:
                    newdata[k] = append(newdata[k], fill_data[k][idx])
        fms, fmsigs, years = getF14CfromDataframe(newdata)
        newdata = {
            'calendaryear': years,
            'bp': 1950 - years,
            'fm': fms,
            'fm_sig': fmsigs
        }
        self.data[label] = newdata
        savepath = Path(self.curve_folder) / f"{label}.json"
        savepath.parent.mkdir(parents=True, exist_ok=True)
        with savepath.open('w', encoding='utf-8') as f:
            json.dump({k: list(v) for k, v in newdata.items()}, f)
        if widget:
            for dataset in widget.datasets:
                dataset.calc.curveData = self
            widget.recalcFlag = True
            for i in range(widget.Ncurves):
                widget.__dict__[f'curveBox{i}'].addItem(label)

            index = widget.curveBox0.findText(label)
            if index != -1:
                widget.curveBox0.setCurrentIndex(index)

            widget.redraw()