import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

header_names = [
    'time',
    'milliseconds',
    'tia',
    'tia_am_scha',
    'tqi_gs_fast_dec',
    'tqi_gs_fast_inc',
    'pv_av',
    'lamb_ls_up[1]',
    'lamb_ls_up[2]',
    'state_eng',
    'teg_dyn_up_cat[1]',
    'teg_dyn_up_cat[2]',
    'fup',
    'fup_sp',
    'pump_vol_vcv',
    'efppwm',
    'fup_efp',
    'iga_av_mv',
    'ti_1_hom[0]',
    'ti_1_hom[3]',
    'amp_mes',
    'map',
    'map_mes',
    'map_1_mes',
    'map_2_mes',
    'pdt_mes',
    'maf',
    'iga_ad_1_knk[0]',
    'iga_ad_1_knk[1]',
    'iga_ad_1_knk[2]',
    'iga_ad_1_knk[3]',
    'iga_ad_l_knk[4]',
    'iga_ad_1_knk[5]',
    'lamb_sp[1]',
    'lamb_sp[2]',
    'tqi_av',
    'gear',
    'vs',
    'cam_sp_ivvt_in',
    'map_sp',
    'rfp_sp',
    'short term fuel trim - bank 1',
    'long term fuel trim - bank 1',
    'short term fuel trim - bank 2',
    'long term fuel trim - bank 2',
    'engine rpm',
    'ignition timing advance for #1 cylinder',
    'ambient air temperature',
    'commanded throttle actuator control'
]

def get_header_index(header):
    for index, string in enumerate(header_names):
        if (string == header):
            return index

def read_sheet(sheet):
    df = pd.read_csv(sheet, header=2, names=header_names)
    return df

def trim_sheet(df):
    df = df.loc[df[df['commanded throttle actuator control'] >= 99.0].index[0]:df[df['commanded throttle actuator control'] >= 99.0].index[-1]]
    df = df.loc[df[df['ignition timing advance for #1 cylinder'] >= 0.0].index[0]:df[df['ignition timing advance for #1 cylinder'] >= 0.0].index[-1]]
    df = df.loc[df[df['lamb_ls_up[1]'] < 1.0].index[0]:df[df['lamb_ls_up[1]'] < 1.0].index[-1]]
    return df

def read_max(df, col):
    return float(df.iloc[:, get_header_index(col)].max())

def read_min(df, col):
    return float(df.iloc[:, get_header_index(col)].min())

def read_knock(df):
    knk0 = round(float(read_min(df, 'iga_ad_1_knk[0]')), 2)
    knk1 = round(float(read_min(df, 'iga_ad_1_knk[1]')), 2)
    knk2 = round(float(read_min(df, 'iga_ad_1_knk[2]')), 2)
    knk3 = round(float(read_min(df, 'iga_ad_1_knk[3]')), 2)
    knk4 = round(float(read_min(df, 'iga_ad_l_knk[4]')), 2)
    knk5 = round(float(read_min(df, 'iga_ad_1_knk[5]')), 2)
    return [knk0, knk1, knk2, knk3, knk4, knk5]

def read_hpfp(df, max_dc):
    hpfp = read_max(df, 'pump_vol_vcv')
    if (hpfp >= max_dc):
        hpfp_maxed = df[df['pump_vol_vcv'] >= max_dc]
        rpm = hpfp_maxed['engine rpm'].values
        gear = hpfp_maxed['gear'].values
        hpfp_dc = []
        for i in range(len(hpfp_maxed)):
            hpfp_dc.append('{}@{}'.format(gear[i], int(rpm[i])))
        return hpfp_dc
    else:
        rpm = df.loc[df['pump_vol_vcv'] == hpfp, 'engine rpm'].values[0]
        gear = df.loc[df['pump_vol_vcv'] == hpfp, 'gear'].values[0]
        return [gear, int(rpm), math.trunc(hpfp * 10) / 10]

def read_hpfp(df, max_dc):
    hpfp = read_max(df, 'pump_vol_vcv')
    if hpfp >= max_dc:
        hpfp_maxed = df[df['pump_vol_vcv'] >= max_dc]
        rpm = hpfp_maxed['engine rpm'].values
        gear = hpfp_maxed['gear'].values
        hpfpv = hpfp_maxed['pump_vol_vcv'].values
        hpfp_dc = []
        for i in range(len(hpfp_maxed)):
            hpfp_dc.append('{}% {}@{}'.format(hpfpv[i], gear[i], int(rpm[i])))
        return hpfp_dc
    else:
        rpm = df.loc[df['pump_vol_vcv'] == hpfp, 'engine rpm'].values[0]
        gear = df.loc[df['pump_vol_vcv'] == hpfp, 'gear'].values[0]
        return ['{}% {}@{}'.format(math.trunc(hpfp * 10) / 10, gear, int(rpm))]

def find_int(lookup_col, cur_col, cur_val):
    return int(df.loc[df[cur_col] == cur_val, '{}'.format(lookup_col)].values[0])

def find_float(lookup_col, cur_col, cur_val):
    return int(df.loc[df[cur_col] == cur_val, '{}'.format(lookup_col)].values[0])

def find_boost(cur_col, cur_val):
    return round(float(df.loc[df[cur_col] == cur_val, 'map_mes'].values[0] - df.loc[df[cur_col] == cur_val, 'amp_mes'].values[0]) * 0.0145, 1)

df = read_sheet('E40 1320ft.csv')
df = trim_sheet(df)

#print(int(read_max(df, 'engine rpm')), 'rpm in gear', find_int('gear', 'engine rpm', read_max(df, 'engine rpm')))
#print(round(read_max(df, 'ignition timing advance for #1 cylinder'), 1), '˚ timing advance in gear', find_int('gear', 'ignition timing advance for #1 cylinder', read_max(df, 'ignition timing advance for #1 cylinder')), 'at', find_int('engine rpm', 'ignition timing advance for #1 cylinder', read_max(df, 'ignition timing advance for #1 cylinder')), 'rpm,', find_boost('ignition timing advance for #1 cylinder', read_max(df, 'ignition timing advance for #1 cylinder')), 'psi')
#print(min(read_knock(df)), '˚ worst knock in cylinder', read_knock(df).index(min(read_knock(df))), 'in gear', find_int('gear', 'iga_ad_1_knk[{}]'.format(read_knock(df).index(min(read_knock(df)))), min(read_knock(df))), 'at', find_int('engine rpm', 'iga_ad_1_knk[{}]'.format(read_knock(df).index(min(read_knock(df)))), min(read_knock(df))), 'rpm')
#print(round((read_max(df, 'map_mes') - read_max(df, 'amp_mes')) * 0.0145, 1), 'psi peak boost in gear', find_int('gear', 'map_mes', read_max(df, 'map_mes')), 'at', find_int('engine rpm', 'map_mes', read_max(df, 'map_mes')), 'rpm,', find_float('ignition timing advance for #1 cylinder', 'map_mes', read_max(df, 'map_mes')), '˚ advance')
