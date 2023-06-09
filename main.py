import plotly.graph_objects as go
import pandas as pd
import math
import os

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
    'iga_ad_1_knk[4]',
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

def read_max(df, col):
    return float(df.iloc[:, get_header_index(col)].max())

def read_min(df, col):
    return float(df.iloc[:, get_header_index(col)].min())

def read_knock(df):
    knk0 = float(read_min(df, 'iga_ad_1_knk[0]'))
    knk1 = float(read_min(df, 'iga_ad_1_knk[1]'))
    knk2 = float(read_min(df, 'iga_ad_1_knk[2]'))
    knk3 = float(read_min(df, 'iga_ad_1_knk[3]'))
    knk4 = float(read_min(df, 'iga_ad_1_knk[4]'))
    knk5 = float(read_min(df, 'iga_ad_1_knk[5]'))
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

def find_int(df, lookup_col, cur_col, cur_val):
    return int(df.loc[df[cur_col] == cur_val, '{}'.format(lookup_col)].values[0])

def find_float(df, lookup_col, cur_col, cur_val):
    return float(df.loc[df[cur_col] == cur_val, '{}'.format(lookup_col)].values[0])

def find_boost(df, cur_col, cur_val):
    return round(float(df.loc[df[cur_col] == cur_val, 'map_mes'].values[0] - df.loc[df[cur_col] == cur_val, 'amp_mes'].values[0]) * 0.0145, 1)

def graph_time_engine_rpm(logfile, df, columns):
    start_threshold = 99.0
    end_threshold = 99.0
    num_rows = 50

    pull = False
    start_index = 0
    end_index = 0

    for index, row in df.iterrows():
        if row['commanded throttle actuator control'] >= start_threshold and not pull:
            start_index = index
            pull = True
        if pull and row['commanded throttle actuator control'] <= end_threshold:
            end_index = index
            break

    start_point = max(0, start_index - num_rows)
    end_point = min(len(df) - 1, end_index + num_rows)

    trimmed_df = df.iloc[start_point:end_point + 1].copy()
    trimmed_df['time'] = trimmed_df['time'] - trimmed_df['time'].iloc[0]

    fig = go.Figure()

    columns.sort()

    colors = [
        '#FF0000', '#00FF00', '#0000FF',  # Primary colors (red, green, blue)
        '#FFA500', '#FFFF00', '#00FFFF',  # Secondary colors (orange, yellow, cyan)
        '#FFC0CB', '#800080', '#008000',  # Tertiary colors (pink, purple, green)
        '#800000', '#008080', '#000080',  # Darker shades of red, cyan, and blue
        '#FF4500', '#FFD700', '#00FF7F',  # Vivid shades of orange, gold, and chartreuse
        '#FF1493', '#8A2BE2', '#ADFF2F',  # Deep pink, blue violet, and green yellow
        '#B22222', '#00CED1', '#8B008B',  # Brick red, dark turquoise, and dark magenta
        '#DC143C', '#00BFFF', '#FF00FF',  # Crimson, deep sky blue, and magenta
        '#8B0000', '#48D1CC', '#9400D3',  # Dark red, medium turquoise, and dark violet
        '#CD5C5C', '#7FFFD4', '#9932CC',  # Indian red, aquamarine, and dark orchid
        '#FF69B4', '#00FA9A', '#8FBC8F',  # Hot pink, medium spring green, and dark sea green
        '#FF6347', '#40E0D0', '#DA70D6',  # Tomato, turquoise, and orchid
        '#FF7F50', '#00FF8C', '#BA55D3',  # Coral, bright green, and medium orchid
        '#FF4500', '#66CDAA', '#800080',  # Orange red, medium aquamarine, and purple
        '#FF8C00', '#20B2AA', '#9932CC',  # Dark orange, light sea green, and dark orchid
        '#FFD700', '#7FFF00', '#9370DB',  # Gold, chartreuse, and medium purple
        '#FF1493', '#00CED1', '#BA55D3',  # Deep pink, dark turquoise, and medium orchid
        '#B22222', '#00FF7F', '#9400D3',  # Brick red, spring green, and dark violet
        '#CD5C5C', '#32CD32', '#8B008B'   # Indian red, lime green, and dark magenta
    ]

    for i, column in enumerate(columns):
        if column == 'engine rpm':
            color = colors[i % len(colors)]
            hovertemplate = '<b><span style=\'color:{};\'>%{{y}}</span></b>'.format(color)
            fig.add_trace(go.Scatter(x=trimmed_df['time'], y=trimmed_df[column], mode='lines', name=column, hovertemplate=hovertemplate, line=dict(color=color)))
        else:
            color = colors[i % len(colors)]
            hovertemplate = '<b><span style=\'color:{};\'>%{{y}}</span></b>'.format(color)
            fig.add_trace(go.Scatter(x=trimmed_df['time'], y=trimmed_df[column], mode='lines', name=column, visible='legendonly', hovertemplate=hovertemplate, line=dict(color=color)))

    fig.update_layout(
        title='\'{}\''.format(logfile),
        xaxis=dict(title='Time (seconds)', dtick=1),
        hovermode='x unified',
        legend=dict(orientation='v', font=dict(size=8), x=1, y=0.5),
        hoverlabel=dict(namelength=-1),
        plot_bgcolor='white'
    )

    fig.show()

def print_log_summary(df):
    max_engine_rpm = read_max(df, 'engine rpm')
    max_timing_advance = read_max(df, 'ignition timing advance for #1 cylinder')
    min_knock = min(read_knock(df))
    max_boost = round((read_max(df, 'map_mes') - read_max(df, 'amp_mes')) * 0.0145, 1)

    timing_advance_max_rpm = find_int(df, 'engine rpm', 'ignition timing advance for #1 cylinder', max_timing_advance)
    timing_advance_max_boost = find_float(df, 'map_mes', 'ignition timing advance for #1 cylinder', max_timing_advance)
    timing_advance_ambient = find_float(df, 'amp_mes', 'ignition timing advance for #1 cylinder', max_timing_advance)
    timing_advance_max_boost = round((timing_advance_max_boost - timing_advance_ambient) * 0.0145, 1)

    gear_max_engine_rpm = find_int(df, 'gear', 'engine rpm', max_engine_rpm)
    gear_max_timing_advance = find_int(df, 'gear', 'ignition timing advance for #1 cylinder', max_timing_advance)
    gear_most_knock = find_int(df, 'gear', 'iga_ad_1_knk[{}]'.format(read_knock(df).index(min_knock)), min_knock)
    gear_peak_boost = find_int(df, 'gear', 'map_mes', read_max(df, 'map_mes'))

    boost_max_engine_rpm = find_int(df, 'engine rpm', 'map_mes', read_max(df, 'map_mes'))
    boost_max_timing_advance = find_float(df, 'ignition timing advance for #1 cylinder', 'map_mes', read_max(df, 'map_mes'))

    knonk_min_engine_rpm = find_int(df, 'engine rpm', 'iga_ad_1_knk[{}]'.format(read_knock(df).index(min_knock)), min_knock)

    print()
    print(int(max_engine_rpm), 'rpm in gear', gear_max_engine_rpm)
    print(max_timing_advance, '˚ timing advance in gear', gear_max_timing_advance, 'at', timing_advance_max_rpm, 'rpm,', timing_advance_max_boost, 'psi')
    print(round(min_knock, 2), '˚ worst knock in cylinder', read_knock(df).index(min_knock), 'in gear', gear_most_knock, 'at', knonk_min_engine_rpm, 'rpm')
    print(max_boost, 'psi peak boost in gear', gear_peak_boost, 'at', boost_max_engine_rpm, 'rpm,', boost_max_timing_advance, '˚ advance')

def main():
    directory = os.getcwd()
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            logfile = os.path.join(directory, filename)
            df = read_sheet(logfile)
            df = df.dropna(how='any')
            print_log_summary(df)
            graph_time_engine_rpm(os.path.basename(logfile), df, header_names[2:])
            return
            
if __name__ == '__main__':
    main()
