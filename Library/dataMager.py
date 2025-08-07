import copy
from Library.HelperFunctions import *
from numpy import array, exp, log, arange, nan, zeros, random, ones, sin, where,full, sqrt, argsort, unique, cumsum, prod, float64, sum as npsum, empty, asarray, pi, abs as npabs, argmax,searchsorted
from scipy.stats import chi2
import pathlib
from PyQt5.QtWidgets import QFileDialog
from pathlib import Path
import pickle
from PyQt5.QtWidgets import QMessageBox
import pandas as pd
from scipy.interpolate import interp1d
from Library.timer import timer
from joblib import Parallel, delayed
from scipy.stats import norm
from matplotlib import pyplot as plt

default_plot_settings = {'dataName':'New Data','colors': ['C0','C0'],'plotbools': [True,True],'showfits':[True,False],'colorbools': [False,False],'plotbool':True,'buttonColors':['#ff5500','#000000'],'chronology':False}
default_offset_settings = {'Manual':True,'offset':0,'offset_sig':0,'min':-100,'max':100,'step':1,'GaussianPrior':True,'mu':0,'sigma':50}

class Calculator:
    def __init__(self,curveManager):
        self.fm = False
        self.curveData = curveManager
        self.curves = self.curveData.curves
        self.data = {}
        for curve in self.curves:
            self.data[curve] = {}
        self.plotsettings = default_plot_settings
        self.offset_settings = default_offset_settings
        self.gauss = False
        self.syntherror = 1.5
        self.amp = 0.8
        self.wiggledata = {}
        self.wiggledata['label'] = array(['Sample 1', 'Sample 2', 'Sample 3'],dtype='U25')
        self.wiggledata['year'] = array([1800, 1801, 1802])
        self.wiggledata['age'] = array([182, 163, 185])
        self.wiggledata['age_sig'] = array([15, 14, 14])
        self.wiggledata['dt'] = self.wiggledata['year']-max(self.wiggledata['year'])
        self.wiggledata['fm'] = exp(-self.wiggledata['age'] / 8033)
        self.wiggledata['fm_sig'] = self.wiggledata['age_sig'] / 8033 * self.wiggledata['fm']
        self.wiggledata['active'] = full(len(self.wiggledata['year']),True)
        self.wiggledata['range'] = full(len(self.wiggledata['year']),5)
        self.offset=0
        self.shift=0
        self.offset_sig = 0
        self.recalc_all()

    def recalc_wiggledata(self,fm=True):
        if fm:
            self.wiggledata['fm'] = exp(-self.wiggledata['age'] / 8033)
            self.wiggledata['fm_sig'] = self.wiggledata['age_sig'] / 8033 * self.wiggledata['fm']
        else:
            self.wiggledata['age'] = -8033 * log(self.wiggledata['fm'])
            self.wiggledata['age_sig'] = 8033 / self.wiggledata['fm'] * self.wiggledata['fm_sig']
        #activeinds = where(self.wiggledata['active'] == True)
        years = self.wiggledata['year'][self.wiggledata['active']]
        if len(years)>0:
            self.wiggledata['dt'] = self.wiggledata['year'] - max(self.wiggledata['year'][self.wiggledata['active']])
        else:
            self.wiggledata['dt'] = self.wiggledata['year']-max(self.wiggledata['year'])


    def calc_bayesian_prob(self):
        N = len(self.wiggledata['year'])
        active = self.wiggledata['active']
        for curve in self.curves:
            if curve not in self.data:
                self.data[curve] = {}
            if curve is None:
                continue
            ps = self.data[curve]['ps']
            tyears = self.data[curve]['tyears']
            dt = abs(tyears[1] - tyears[0])
            active_mask = array(active, dtype=bool)
            pt = prod(ps[active_mask], axis=0)
            pt /= sum(pt)
            p_squared_sums = npsum(ps ** 2, axis=1) * dt
            A_is = npsum(pt * ps * dt, axis=1) / p_squared_sums
            A = prod(A_is[active_mask]) ** (1 / sqrt(len(ps[active_mask])))
            A_n = 1 / sqrt(2 * len(ps[active_mask]))
            self.data[curve]['probability'] = pt
            self.data[curve]['ps'] = ps
            self.data[curve]['A'] = A
            self.data[curve]['A_n'] = A_n
            self.wiggledata[f'{curve}A_i'] = A_is
            self.data[curve]['Offset'] = self.offset

    def recalc_all(self):
        self.offset = self.offset_settings['offset']
        self.offset_sig = self.offset_settings['offset_sig']
        for curve in self.curves:
            if curve is not None:
                if curve not in self.data:
                    self.data[curve] = {}
        if self.offset_settings['Manual']:
            self.calcOffset()
            self.calc_probs()
            #self.calc_probs_with_ranges()
            self.calc_bayesian_prob()
        else:
            self.calc_probs_with_offsetfit()
        self.calc_percentile_ranges()

    @timer
    def calc_probs_with_offsetfit(self):
        self.curves = self.curveData.curves
        wiggleyears = self.wiggledata['year']
        wigglefms = self.wiggledata['fm']
        wigglefms_sig = self.wiggledata['fm_sig']
        testoffsets = arange(self.offset_settings['min'], self.offset_settings['max'], self.offset_settings['step'])
        N = len(wiggleyears)
        if self.offset_settings['GaussianPrior']:
            offsetprior = norm.pdf(testoffsets, loc=self.offset_settings['mu'], scale=self.offset_settings['sigma'])
            offsetprior /= offsetprior.sum()
        else:
            offsetprior = ones(len(testoffsets)) / len(testoffsets)
        shiftyears = self.wiggledata['dt']
        for curve in self.curves:
            if curve is None:
                continue
            maxsig = 10 * max(wigglefms_sig)
            minfmsearch = min(wigglefms - maxsig)
            maxfmsearch = max(wigglefms + maxsig)
            fms = self.curveData.data[curve]['fm']
            fm_sigs = self.curveData.data[curve]['fm_sig']
            t = self.curveData.data[curve]['calendaryear']
            indexes = where((fms >= minfmsearch) & (fms < maxfmsearch))[0]
            indexes = arange(min(indexes), max(indexes), 1)
            years = t[indexes]
            minyear, maxyear = min(years) - min(shiftyears), max(years) - max(shiftyears)
            tyears = arange(minyear, maxyear, 1)
            self.data[curve]['tyears'] = tyears
            curvefm = interp1d(t, fms, assume_sorted=True)
            curvefm_sig = interp1d(t, fm_sigs, assume_sorted=True)
            len_ty = len(tyears)
            len_wig = len(wiggleyears)
            len_off = len(testoffsets)
            likelyhoods = zeros((len_off, len_ty))
            ps_likelihood = empty((len_off, len_wig, len_ty))
            tyears = asarray(tyears)
            for j, offset in enumerate(testoffsets):
                ps = empty((len_wig, len_ty))
                for i in range(len_wig):
                    dt = shiftyears[i]
                    age = -8033 * log(wigglefms[i]) + offset
                    Ri = exp(-age / 8033)
                    dRi = wigglefms_sig[i]
                    shifted_years = tyears + dt
                    R = curvefm(shifted_years)
                    dR = curvefm_sig(shifted_years)
                    denom = 2 * dRi ** 2 + 2 * dR ** 2
                    diff = Ri - R
                    p_i = exp(-diff ** 2 / denom) / (dRi ** 2 + dR ** 2) ** 0.5
                    p_i = p_i / npsum(p_i)
                    ps_likelihood[j, i] = p_i * offsetprior[j]
                    ps[i, :] = -0.5 * ((Ri - R) ** 2 / (dRi ** 2 + dR ** 2)) - 0.5 * log(
                        2 * pi * (dRi ** 2 + dR ** 2)) + log(offsetprior[j])
                activeps = ps[self.wiggledata['active'], :]
                pt = npsum(activeps, axis=0)
                likelyhoods[j] = pt
            likelyhoods = exp(likelyhoods)  #
            weighted_likelihood = likelyhoods  # offsetprior[:, np.newaxis]
            posterior_age = npsum(weighted_likelihood, axis=0)
            posterior_age /= npsum(posterior_age)
            posterior_offset = npsum(weighted_likelihood, axis=1)
            posterior_offset /= npsum(posterior_offset)
            dt_step = npabs(tyears[1] - tyears[0])
            ps = npsum(ps_likelihood, axis=0)
            A_is = empty(len_wig)
            for i in range(len_wig):
                p = ps[i] / sum(ps[i])
                a = npsum(posterior_age * p) * dt_step
                b = npsum(p ** 2) * dt_step
                A_is[i] = a / b
            A = prod(A_is) ** (1 / sqrt(len_wig))
            A_n = 1 / (2 * len_wig) ** 0.5
            self.data[curve]['probability'] = posterior_age
            self.data[curve]['ps'] = ps
            self.data[curve]['A'] = A
            self.data[curve]['A_n'] = A_n
            self.data[curve]['offsetprob'] = posterior_offset
            self.data[curve]['offsetps'] = ps_likelihood
            self.wiggledata[f'{curve}A_i'] = A_is
            offset = testoffsets[argmax(posterior_offset)]
            cdf = cumsum(posterior_offset)
            offset_sig = testoffsets[searchsorted(cdf, 0.84)]-testoffsets[searchsorted(cdf, 0.16)]
            age_corr = -8033 * log(self.wiggledata['fm']) + offset
            age_sig = 8033 / self.wiggledata['fm'] * self.wiggledata['fm_sig']
            sig_corr = (age_sig ** 2 + offset_sig ** 2) ** 0.5
            self.data[curve]['fm_corr'] = exp(-age_corr / 8033)
            self.data[curve]['fm_sig_corr'] = self.data[curve]['fm_corr']  / 8033 * sig_corr
            self.data[curve]['offset'] = offset
            self.data[curve]['offset_sig'] = offset_sig

    @timer
    def calc_probs(self):
        self.curves = self.curveData.curves
        wiggleyears = self.wiggledata['year']
        wigglefms = self.wiggledata['fm_corr']
        wigglefms_sig = self.wiggledata['fm_sig_corr']
        N = len(wiggleyears)
        shiftyears = self.wiggledata['dt']
        def process_curve(curve):
            if curve is None:
                return curve, None
            if curve not in self.data:
                self.data[curve] = {}
            if len(wigglefms_sig) == 0:
                self.data[curve]['tyears'] = full(2, nan)
                self.data[curve]['ps'] = full(shape=(2, N), fill_value=nan)
                return curve, self.data[curve]
            maxsig = 10 * max(wigglefms_sig)
            minfmsearch = min(wigglefms - maxsig)
            maxfmsearch = max(wigglefms + maxsig)
            fms = self.curveData.data[curve]['fm']
            fm_sigs = self.curveData.data[curve]['fm_sig']
            t = self.curveData.data[curve]['calendaryear']
            indexes = where((fms >= minfmsearch) & (fms < maxfmsearch))[0]
            if len(indexes) == 0:
                self.data[curve]['tyears'] = full(2, nan)
                self.data[curve]['ps'] = full(shape=(2, N), fill_value=nan)
                return curve, self.data[curve]
            indexes = arange(min(indexes), max(indexes), 1)
            years = t[indexes]
            if len(years) == 0:
                self.data[curve]['tyears'] = full(2, nan)
                self.data[curve]['ps'] = full(shape=(2, N), fill_value=nan)
                return curve, self.data[curve]
            minyear, maxyear = min(years) - min(shiftyears), max(years) - max(shiftyears)
            tyears = arange(minyear, maxyear, 1)
            self.data[curve]['tyears'] = tyears
            curvefm = interp1d(t, fms, assume_sorted=True)
            curvefm_sig = interp1d(t, fm_sigs, assume_sorted=True)
            M = len(tyears)
            Ri = ones((N, M)) * wigglefms[:, None]
            dRi = ones((N, M)) * wigglefms_sig[:, None]
            dR = zeros((N, M))
            R = zeros((N, M))
            ps = zeros((N, M), dtype=float64)
            R[:] = curvefm(tyears + shiftyears[:, None])
            dR[:] = curvefm_sig(tyears + shiftyears[:, None])
            dRi2 = dRi ** 2
            dR2 = dR ** 2
            denom = (2 * dRi2 + 2 * dR2) ** 0.5
            ps[:] = exp(-((Ri - R) ** 2) / (2 * dRi2 + 2 * dR2)) / denom
            ps /= ps.sum(axis=1, keepdims=True)
            self.data[curve]['ps'] = ps
            return curve, self.data[curve]
        for curve in self.curves:
            c, data = process_curve(curve)
            if data is not None:
                self.data[curve] = data

    def calcOffset(self):
        age_corr = -8033*log(self.wiggledata['fm'])+self.offset
        age_sig = 8033/self.wiggledata['fm']*self.wiggledata['fm_sig']
        sig_corr = (age_sig**2+self.offset_sig**2)**0.5

        self.wiggledata['fm_corr'] = exp(-age_corr/8033)
        self.wiggledata['fm_sig_corr'] = self.wiggledata['fm_corr']/8033*sig_corr
        self.wiggleyears = self.wiggledata['year'][self.wiggledata['active']]
        self.wigglefms = self.wiggledata['fm_corr'][self.wiggledata['active']]
        self.wigglefms_sig = self.wiggledata['fm_sig_corr'][self.wiggledata['active']]
        for curve in self.curves:
            if curve is not None:
                self.data[curve]['fm_corr'] = exp(-age_corr / 8033)
                self.data[curve]['fm_sig_corr'] = self.wiggledata['fm_corr'] / 8033 * sig_corr

    def load_data(self,dataSetManager):
        start_folder = 'Library\\Data\\Wiggledata'
        file_path, _ = QFileDialog.getOpenFileName(dataSetManager.widget, "Open File", start_folder,
                                                   "All Files (*);;Excel files(*.xlsx)")
        dataSetManager.tableModel.layoutAboutToBeChanged.emit()
        label = Path(file_path).stem
        savedata = copy.copy(self.wiggledata)
        # Display selected file path
        if file_path:
            pass
        else:
            return
        df = loadexcel(file_path)
        newwiggledata = {}
        keys = ['year','age','age_sig','fm','fm_sig']
        datakeys = list(df.keys())
        if 'age' in datakeys and 'age_sig' in datakeys:
            newwiggledata['age'] = df['age']
            newwiggledata['age_sig'] = df['age_sig']
            fmcalc = True
        elif 'fm' in datakeys and 'fm_sig' in datakeys:
            newwiggledata['fm'] = df['fm']
            newwiggledata['fm_sig'] = df['fm_sig']
            fmcalc = False
        else:
            QMessageBox.warning(None, "Invalid headers in the file",
                                "Header most include 'age' or 'age_sig'")
            return
        if 'year' in datakeys:
            newwiggledata['year'] = df['year']
        elif 'bp' in datakeys:
            newwiggledata['year'] = 1950-df['bp']
        else:
            QMessageBox.warning(None, "Invalid headers in the file",
                                "Please enter a valid number.")
            return
        if 'range' in datakeys:
            newwiggledata['range'] = df['range']
        else:
            newwiggledata['range'] = ones(len(df['year']),dtype=int)
        newwiggledata['dt'] = newwiggledata['year'] - max(newwiggledata['year'])
        newwiggledata['active'] = full(len(newwiggledata['year']), True)
        self.wiggledata = newwiggledata
        for key in datakeys:
            if key not in keys:
                self.wiggledata[key] = df[key]
        if 'label' not in self.wiggledata.keys():
            self.wiggledata['label'] = copy.copy(self.wiggledata['year'])
        self.recalc_wiggledata(fm=fmcalc)
        self.dataName = label
        self.recalc_all()
        dataSetManager.tableModel.layoutChanged.emit()
        model = dataSetManager.tableModel
        model.data = self.wiggledata
        model.sort(model.sort_column,model.order)
        dataSetManager.tabWidget.setTabText(dataSetManager.tabIndex, self.dataName)
        self.plotsettings['dataName'] = label
        dataSetManager.widget.redraw()

    def calc_percentile_ranges(self):
        self.percentiles = [0.95]
        for curve in self.curves:
            if curve not in self.data:
                self.data[curve] = {}
            if curve is None:
                continue
            pt = self.data[curve]['probability']
            sortind = argsort(pt)[::-1]
            revsortind = argsort(sortind)
            sortp = pt[sortind]
            cdf = cumsum(sortp)
            for percentile in self.percentiles:
                mask = cdf<percentile
                self.data[curve][f'{percentile}%range'] = mask[revsortind]


