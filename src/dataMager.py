import copy
from src.HelperFunctions import *
from numpy import (array, exp, log, arange, nan, zeros, ones, where, full, sqrt, argsort, cumsum, prod, float64, mean,
                   sum as npsum, empty, asarray, pi, abs as npabs, argmax, max as npmax, min as npmin, absolute,
                   searchsorted, interp as npinterp)
from numba import njit, prange
from PyQt5.QtWidgets import QFileDialog
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox
from scipy.interpolate import interp1d
from src.timer import timer
from scipy.stats import norm
from scipy.special import logsumexp
import numpy as np

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

    def calc_bayesian_posterior(self):
        N = len(self.wiggledata['year'])
        active = self.wiggledata['active']
        for curve in self.curves:
            if curve not in self.data:
                self.data[curve] = {}
            if curve is None:
                continue
            ps = self.data[curve]['ps']
            logps = self.data[curve]['logps']
            tyears = self.data[curve]['tyears']
            dt = abs(tyears[1] - tyears[0])
            active_mask = array(active, dtype=bool)
            posterior = npsum(logps[active_mask], axis=0)
            posterior = posterior-npmax(posterior)
            pt = exp(posterior)
            pt /= sum(pt)
            p_squared_sums = npsum(ps ** 2, axis=1) * dt
            A_is = npsum(pt * ps * dt, axis=1) / p_squared_sums
            A = prod(A_is[active_mask]) ** (1 / sqrt(len(ps[active_mask])))
            A_n = 1 / sqrt(2 * len(ps[active_mask]))
            self.data[curve]['probability'] = pt
            self.data[curve]['probability2'] = pt
            self.data[curve]['A'] = A
            self.data[curve]['A_n'] = A_n
            self.wiggledata[f'{curve}A_i'] = A_is
            self.data[curve]['Offset'] = self.offset

    @timer
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
        else:
            self.calc_probs_with_offsetfit()
        self.calc_posterior_distribution()
        self.calc_percentile_ranges()

    @timer
    def calc_posterior_distribution(self):
        if self.offset_settings['Manual']:
            self.calc_bayesian_posterior()
        else:
            self.calcBayesianPosterior_Offset()
    @timer
    def calc_probs_with_offsetfit(self):
        self.curves = self.curveData.curves
        wigglefms = self.wiggledata['fm']
        wigglefms_sig = self.wiggledata['fm_sig']
        testoffsets = arange(self.offset_settings['min'], self.offset_settings['max'], self.offset_settings['step'])
        if self.offset_settings['GaussianPrior']:
            offsetprior = norm.pdf(testoffsets, loc=self.offset_settings['mu'], scale=self.offset_settings['sigma'])*self.offset_settings['step']
            offsetprior /= offsetprior.sum()
        else:
            offsetprior = ones(len(testoffsets)) / len(testoffsets)
        shiftyears = self.wiggledata['dt']
        for curve in self.curves:
            if curve is None:
                continue
            maxsig = 15 * max(wigglefms_sig)
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
            #len_ty = len(tyears)
            #len_wig = len(wiggleyears)
            #len_off = len(testoffsets)
            shifted_years = tyears[None, :] + shiftyears[:, None]  # (len_wig, len_ty)
            R = curvefm(shifted_years)[None, :, :]   # (1, len_wig, len_ty)
            dR = curvefm_sig(shifted_years)[None, :, :]   # (1, len_wig, len_ty)
            dRi = wigglefms_sig[:, None][None, :, :]   # (1, len_wig, 1)
            offsets = testoffsets[:, None, None]  # (len_off, 1, 1)  # (len_off, 1, 1)
            log_offsets_prior = np.log(offsetprior)
            ages = -8033 * np.log(wigglefms[None, :, None]) + offsets  # (len_off, len_wig, 1)
            Ri = np.exp(-ages / 8033)  # (len_off, len_wig, 1)
            log_pi = -(Ri - R) ** 2 / (2 * dRi ** 2 + 2 * dR ** 2) - 0.5 * np.log(2 * np.pi * (dRi ** 2 + dR ** 2))  # (len_off, len_wig, len_ty)
            ps_loglikelihoods = log_pi + log_offsets_prior[:, None, None] # (len_off, len_wig, len_ty)
            self.data[curve]['ps_loglikelihoods'] = ps_loglikelihoods
            self.data[curve]['testoffsets'] = testoffsets
            self.data[curve]['offsetprior'] = offsetprior

    @timer
    def calcBayesianPosterior_Offset(self):
        active_idx = self.wiggledata['active']
        len_wig = len(self.wiggledata['year'])
        for curve in self.curves:
            if curve not in self.data:
                self.data[curve] = {}
            if curve is None:
                continue
            testoffsets = self.data[curve]['testoffsets']
            tyears = self.data[curve]['tyears']
            ps_loglikelihoods = self.data[curve]['ps_loglikelihoods']#(len_off, len_wig, len_ty)
            n_active = sum(active_idx)
            active_ps = ps_loglikelihoods[:, active_idx, :]  # (len_off, n_active, len_ty)
            loglikelyhoods = np.sum(active_ps, axis=1)
            max_loglike = npmax(loglikelyhoods)
            shifted = loglikelyhoods - max_loglike
            likelyhoods = exp(shifted)
            posterior_age_log = logsumexp(loglikelyhoods, axis=0)# (len_ty)
            posterior_offset_log = logsumexp(loglikelyhoods, axis=1)# (len_off)
            posterior_age = exp(posterior_age_log - logsumexp(posterior_age_log))
            posterior_offset = exp(posterior_offset_log - logsumexp(posterior_offset_log))
            dt_step = npabs(tyears[1] - tyears[0])
            max_loglike = npmax(ps_loglikelihoods)
            shifted = ps_loglikelihoods - max_loglike
            ps_likelihoods = exp(shifted)
            posterior_offset_log_expanded = posterior_offset_log[:, None, None]
            posterior_ps_loglikelihoods = ps_loglikelihoods + posterior_offset_log_expanded
            log_ps = logsumexp(posterior_ps_loglikelihoods, axis=0)
            #log_ps = logsumexp(ps_loglikelihoods, axis=0)
            log_norms = logsumexp(log_ps, axis=1, keepdims=True)
            ps = exp(log_ps - log_norms)
            A_is = empty(len_wig)
            for i,p in enumerate(ps):
                a = npsum(posterior_age * p) * dt_step
                b = npsum(p ** 2) * dt_step
                A_is[i] = a / b
            A_is_active = A_is[active_idx]
            #A_overall = prod(A_is_active) ** (1 / sqrt(n_active))
            A_overall = np.exp(mean(log(A_is_active)))
            A_n = 1 / (2 * n_active) ** 0.5
            offset = testoffsets[argmax(posterior_offset)]
            cdf = cumsum(posterior_offset)
            offset_sig = testoffsets[searchsorted(cdf, 0.84)] - testoffsets[searchsorted(cdf, 0.16)]
            age_corr = -8033 * log(self.wiggledata['fm']) + offset
            age_sig = 8033 / self.wiggledata['fm'] * self.wiggledata['fm_sig']

            self.data[curve]['probability'] = posterior_age
            self.data[curve]['probability2'] = posterior_age
            self.data[curve]['ps'] = ps
            self.data[curve]['logps'] = log_ps
            self.data[curve]['A'] = A_overall
            self.data[curve]['A_n'] = A_n
            self.data[curve]['offsetprob'] = posterior_offset
            self.data[curve]['offsetps'] = ps_likelihoods
            self.data[curve]['likelihoods'] = likelyhoods
            self.data[curve]['loglikelihoods'] = loglikelyhoods
            self.wiggledata[f'{curve}A_i'] = A_is
            self.data[curve]['fm_corr'] = exp(-age_corr / 8033)
            self.data[curve]['fm_sig_corr'] = self.wiggledata['fm_sig']
            self.data[curve]['offset'] = offset
            self.data[curve]['offset_sig'] = offset_sig

    def returnNan(self):
        data = {}
        N = len(self.wiggledata['year'])
        data['tyears'] = full(2, nan)
        data['ps'] = full(shape=(2, N), fill_value=nan)
        data['logps'] = full(shape=(2, N), fill_value=nan)
        return data

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
                return curve, self.returnNan()
            maxsig = 20 * max(wigglefms_sig)
            minfmsearch = min(wigglefms - maxsig)
            maxfmsearch = max(wigglefms + maxsig)
            fms = self.curveData.data[curve]['fm']
            fm_sigs = self.curveData.data[curve]['fm_sig']
            t = self.curveData.data[curve]['calendaryear']
            indexes = where((fms >= minfmsearch) & (fms < maxfmsearch))[0]
            if len(indexes) == 0:
                return curve, self.returnNan()
            indexes = arange(min(indexes), max(indexes), 1)
            years = t[indexes]
            if len(years) == 0:
                return curve, self.returnNan()
            minyear, maxyear = min(years), max(years)
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
            logps = -((Ri - R) ** 2) / (2 * dRi2 + 2 * dR2)-log(denom)
            ps[:] = exp(-((Ri - R) ** 2) / (2 * dRi2 + 2 * dR2)) / denom

            ps /= ps.sum(axis=1, keepdims=True)
            self.data[curve]['ps'] = ps
            self.data[curve]['logps'] = logps
            self.data[curve]['offset'] = self.offset
            self.data[curve]['offset_sig'] = self.offset_sig
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

@njit(fastmath=True, parallel=True)
def _compute_log_ps_and_active(Ri_ow, dRi_w, R_wt, dR_wt, log_prior_o, is_active_w):
    O = Ri_ow.shape[0]
    W = Ri_ow.shape[1]
    T = R_wt.shape[1]
    log_ps = zeros((O, W, T))
    active_sum = zeros((O, T))
    two_pi = 2.0 * pi
    for j in prange(O):  # offsets
        lp = log_prior_o[j]
        for i in range(W):  # wiggles
            ri = Ri_ow[j, i]
            d_ri = dRi_w[i]
            for k in range(T):  # tyears
                r = R_wt[i, k]
                d_r = dR_wt[i, k]
                var = d_ri * d_ri + d_r * d_r
                diff = ri - r
                val = -0.5 * (diff * diff / var) - 0.5 * log(two_pi * var) + lp
                log_ps[j, i, k] = val
                if is_active_w[i]:
                    active_sum[j, k] += val
    return log_ps, active_sum




