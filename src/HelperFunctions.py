
from numpy import array, argsort, sort, unique, where
import pandas as pd
import math
import random

def groupdf(df, groupkey):
    data = {}
    for key in df.keys():
        data[key] = array(df[key])
    _, idx = unique(data[groupkey], return_index=True)
    keys = data[groupkey][sort(idx)]
    result = {}
    for key in keys:
        idx = where(data[groupkey] == key)
        result[key] = {}
        for key2 in data.keys():
            result[key][key2] = data[key2][idx]
    return result

def sortdf(df, sortkey):
    sortind = argsort(df[sortkey])
    for key in df.keys():
        df[key] = df[key][sortind]
    return df

def loadexcel(filename):
    edf = pd.read_excel(filename)
    df = {}
    for key in edf:
        df[key] = array(edf[key])
    return df

def fast_random_combinations(input_list, r, n):
    if r > len(input_list):
        raise ValueError("r cannot be larger than the length of the input list.")

    combis = math.comb(len(input_list),r)
    if n > combis:
        n = combis
    result = set()
    while len(result) < n:
        # Generate a single random combination by sampling r unique elements
        combo = tuple(sorted(random.sample(list(input_list), r)))
        result.add(combo)

    return list(result)

def getF14CfromDataframe(df):
    fms = []
    fm_sigs = []
    years = []
    for i,time in enumerate(df['bp']):
        df['bp'][i] = round(time,0)
    bpdf = groupdf(df, 'bp')
    halftime = 8267
    for i,bp in enumerate(bpdf.keys()):
        N = len(bpdf[bp]['fm'])
        weight = 1/bpdf[bp]['fm_sig']**2
        fm = float(sum(weight*bpdf[bp]['fm'])/sum(weight))
        fm_sig = float(sum(weight ** 2 * bpdf[bp]['fm_sig'] ** 2) ** 0.5) / sum(weight)
        fbp = float(bp)
        years.append(1950-fbp)
        fms.append(fm)
        fm_sigs.append(fm_sig)
    fms = array(fms)
    fm_sigs = array(fm_sigs)
    years = array(years)
    sortind = argsort(years)
    years = years[sortind]
    fms = fms[sortind]
    fm_sigs = fm_sigs[sortind]
    return fms, fm_sigs, years