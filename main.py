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

def read_row(df, row):
    return df.iloc[row]

def read_col(df, col):
    return df.iloc[:, get_header_index(col)]

def read_value(df, row, col):
    return df.iloc[row, get_header_index(col)]

def read_max(df, col):
    return df.iloc[:, get_header_index(col)].max()

def read_min(df, col):
    return df.iloc[:, get_header_index(col)].min()

def read_knock(df):
    knk0 = round(float(read_min(df, 'iga_ad_1_knk[0]')), 2)
    knk1 = round(float(read_min(df, 'iga_ad_1_knk[1]')), 2)
    knk2 = round(float(read_min(df, 'iga_ad_1_knk[2]')), 2)
    knk3 = round(float(read_min(df, 'iga_ad_1_knk[3]')), 2)
    knk4 = round(float(read_min(df, 'iga_ad_l_knk[4]')), 2)
    knk5 = round(float(read_min(df, 'iga_ad_1_knk[5]')), 2)
    return [knk0, knk1, knk2, knk3, knk4, knk5]

def read_hpfp(df):
    hpfp = read_max(df, 'pump_vol_vcv')
    if (hpfp > 1000):
        hpfp_maxed = df[df['pump_vol_vcv'] > 99]
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

def read_boost(df):
    throttle = read_max(df, 'commanded throttle actuator control')
    if (throttle > 99):
        wot = df[df['commanded throttle actuator control'] > 99]
        boost_actual = wot['map_mes'].values
        ambient = wot['amp_mes'].values
        boost_data = []
        for i in range(len(wot)):
            boost_data.append(int(boost_actual[i] - ambient[i]))
        return boost_data

df = read_sheet('E40 1320ft.csv')
df = df[df['vs'] != 0]
print(df)
input()
df = df[df['commanded throttle actuator control'] > 99.0]
df = df[df['ignition timing advance for #1 cylinder'] > 0.0]
df = df[df['lamb_ls_up[2]'] < 1.0]
print(df)
input()

# Assuming your dataframe is named 'df'

# Calculate actual boost and record gear changes
actual_boost = df.loc[df['commanded throttle actuator control'] > 99, 'map_mes'] - df.loc[df['commanded throttle actuator control'] > 99, 'amp_mes']
gear_changes = df[(df['gear'].diff() > 0) & (df['gear'].diff().notnull())]

# Exclude the first gear change from 0 to 1
gear_changes = gear_changes.iloc[1:]

# Plot actual boost and gear changes
plt.figure(figsize=(10, 6))
plt.plot(actual_boost, label='Actual Boost')
for index, row in gear_changes.iterrows():
    plt.axvline(x=index, color='red', linestyle='--')
plt.title("Actual Boost with Gear Changes")
plt.xlabel("Index")
plt.ylabel("Actual Boost")

# Calculate the step size for y-axis
boost_min = min(actual_boost)
boost_max = max(actual_boost)
gridlines = 20
step = (boost_max - boost_min) / (gridlines - 1)

plt.yticks(np.arange(boost_min, boost_max+step, step))  # Set y-axis ticks
plt.grid(True)  # Display gridlines
plt.legend()

# Display gear changes horizontally
gear_change_ticks = list(gear_changes.index)
gear_change_labels = [f"{int(row['gear']-1)}->{int(row['gear'])}" for _, row in gear_changes.iterrows()]
plt.xticks(gear_change_ticks, gear_change_labels, rotation=0)

plt.show()

input()

print(int(read_max(df, 'engine rpm')), 'rpm')
print(round(read_max(df, 'ignition timing advance for #1 cylinder'), 1), '˚')
print(round(read_min(df, 'iga_ad_1_knk[0]'), 1), '˚')
print(round((read_max(df, 'map_mes') - read_max(df, 'amp_mes')) * 0.0145, 1), 'psi')
print(read_knock(df))
print(read_hpfp(df))
print(read_boost(df))
