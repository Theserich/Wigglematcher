
from numpy import array, argsort, sort, unique, where, exp, log
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

def loadcsv(filename):
    edf = pd.read_csv(filename)
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

def parse_oxcal_file(file_path):
    headers = ['bp', '14C age', 'Sigma1']
    result = {h: [] for h in headers}
    with open(file_path, 'r') as f:
        lines = f.readlines()
    start = True
    second_header = False
    for line in lines:
        if line.lstrip().startswith('#') and start:
            continue
        elif line.lstrip().startswith('#'):
            second_header = True
            continue
        start = False
        line = line.replace('!', '').replace('?', '')
        if not second_header:
            values = line.strip().split(',')
            result['bp'].append(float(values[0]))
            result['14C age'].append(float(values[1]))
            result['Sigma1'].append(float(values[2]))
        else:
            values = line.strip().split('\t')
            bp = 1950 - float(values[0])
            age = -8033 * log(float(values[3]))
            sig = 8033 / float(values[3]) * float(values[4])
            result['bp'].append(bp)
            result['14C age'].append(age)
            result['Sigma1'].append(sig)
    bp = array(result['bp'])
    age = array(result['14C age'])
    sig = array(result['Sigma1'])
    return {
        'bp': bp,
        'fm': exp(-age / 8033),
        'fm_sig': exp(-age / 8033) / 8033 * sig
    }

def parse_dictionary(df):
    keys = df.keys()
    data = {}
    if 'age' in keys and 'age_sig' in keys:
        data['fm'] = exp(-df['age'] / 8033)
        data['fm_sig'] = data['fm'] / 8033 * df['age_sig']
    elif 'fm' in keys and 'fm_sig' in keys:
        data['fm'] = df['fm']
        data['fm_sig'] = df['fm_sig']
    else:
        raise ValueError("Excel or CSV must contain age/age_sig or fm/fm_sig")
    if 'bp' in keys:
        data['bp'] = df['bp']
    elif 'year' in keys:
        data['bp'] = 1950 - df['year']
    elif 'calendaryear' in keys:
        data['bp'] = 1950 - df['calendaryear']
    else:
        raise ValueError("Excel or CSV must contain bp, year, or calendaryear")
    return data

def parse_excel(file_path):
    df = loadexcel(file_path)
    return parse_dictionary(df)

def parse_csv(self, file_path):
    df = loadcsv(file_path)  # pandas or your own loader
    return parse_dictionary(df)


parse_dict = {
    '.xlsx': parse_excel,
    '.csv': parse_csv,
    '.14c': parse_oxcal_file
}

