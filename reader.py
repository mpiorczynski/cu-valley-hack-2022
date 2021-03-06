import pandas as pd
import os
import numpy as np
from scipy import stats


def last_h(df, n_hours):
    temp = df['temp_zuz'].copy()
    for n in range(1, n_hours + 1):
        label = 'temp_last' + '_' + str(n)
        df[label] = temp.fillna(method='ffill').shift(periods=1 + 60 * (n - 1))


def read_dataframe(dirpath, excel_file_path, temperature_file_path):
    """This function creates a pandas dataframe in which there are given temperature and other data as
    'TEMP.11 POD 2 WARSTWĄ WYMURÓWKI' and so on. The index is timestamp. Each index is given hour in given day.

    dirpath is directory to folder, where are all .gz files, like 'avg_from_2020_10_01_00_00_00_to_2020_10_01_23_59_00.gz'
    in this directory there can't be any other files, like variables_description

    excel_file_path is filepath to excel file with variables descriptions

    temperature_file_path is filepath to .csv file with temperature of heater
    """

    df = pd.concat([pd.read_csv(os.path.join(dirpath, fname))
                    for fname in os.listdir(dirpath)], ignore_index=True)

    df['czas'] = df['czas'].str[:19]
    df['czas'] = pd.to_datetime(df['czas'], format='%Y-%m-%d %H:%M:%S')

    col_df = pd.read_excel(excel_file_path)
    col_df['opis'] = col_df['opis'] + ' ' + col_df['Jednostka']
    col_df.drop(columns=['Jednostka'], inplace=True)

    names_dict = col_df.set_index('Tagname').to_dict()['opis']
    names_dict = {k.lower(): v for k, v in names_dict.items()}

    # df.rename(columns=names_dict, inplace=True)

    temp = pd.read_csv(temperature_file_path, delimiter=';')
    temp.rename(columns={'Czas': 'czas'}, inplace=True)
    temp['czas'] = pd.to_datetime(temp['czas'])
    merged = pd.merge(df, temp, how='left', on='czas')

    return merged


def remove_when_off(df, min_off=1270, margin=15, by='temp_zuz'):
    """This function removes from given data dataframes all records when heater was off. It remove all records in which
    given feater (described by by argument) was lower or equal to min_off plus margin number of records below or after
    this record.

    Return:
        Function returns view on new dataframe whem heater was off

    """

    what = np.full(df.shape[0], True)
    temp_series = df[by]
    max_idx = df.shape[0] - 1
    for index, (date, temp) in enumerate(temp_series.iteritems()):
        if temp <= min_off:
            from_idx, to_idx = index - margin, index + margin
            if from_idx < 0: from_idx = 0
            if to_idx > max_idx: to_idx = max_idx
            what[from_idx:to_idx] = False
    return df[what]


def read(dirpath, excel_file_path, temperature_file_path):
    merged = read_dataframe(dirpath, excel_file_path, temperature_file_path)
    df = merged.copy()
    df.set_index(['czas'], inplace=True)
    df = df[~df.index.duplicated()]
    df = df.asfreq('T')
    last_h(df, 4)

    cols = list(df.columns)
    cols.remove('temp_zuz')

    df = df.dropna(subset=cols)

    col_names = ['001fcx00211.pv',
                 '001fcx00221.pv',
                 '001fcx00231.pv',
                 '001fcx00241.pv',
                 '001fir01307.daca.pv',
                 '001fir01308.daca.pv',
                 '001fir01309.daca.pv',
                 '001fir01310.daca.pv',
                 '001fir01311.daca.pv',
                 '001fir01312.daca.pv',
                 '001fir01313.daca.pv',
                 '001fir01315.daca.pv',
                 '001nir0szr0.daca.pv',
                 '001tir01357.daca.pv',
                 '001tir01358.daca.pv',
                 '001tir01359.daca.pv']

    new_df = df.copy()

    new_df = pd.concat(
        [new_df, new_df[col_names].rename(columns=lambda col_name: f'{col_name}_avg_00-15').rolling(window=15).mean()],
        axis=1)
    new_df = pd.concat([new_df, new_df[col_names].shift(periods=15, freq='min').rename(
        columns=lambda col_name: f'{col_name}_avg_15-30').rolling(window=15).mean()], axis=1)
    new_df = pd.concat([new_df, new_df[col_names].shift(periods=30, freq='min').rename(
        columns=lambda col_name: f'{col_name}_avg_30-45').rolling(window=15).mean()], axis=1)
    new_df = pd.concat([new_df, new_df[col_names].shift(periods=45, freq='min').rename(
        columns=lambda col_name: f'{col_name}_avg_45-60').rolling(window=15).mean()], axis=1)

    correlated_cols = ['001fcx00221.pv', '001fir01307.daca.pv', '001fir01308.daca.pv',
                       '001fir01309.daca.pv', '001fir01310.daca.pv', '001fir01311.daca.pv',
                       '001fir01312.daca.pv', '001fir01315.daca.pv', '001nir0szr0.daca.pv',
                       '001tix01063.daca.pv', '001tix01065.daca.pv', '001tix01067.daca.pv',
                       '001tix01068.daca.pv', '001tix01071.daca.pv', '001tix01072.daca.pv',
                       '001tix01073.daca.pv', '001tix01074.daca.pv', '001tix01075.daca.pv',
                       '001tix01079.daca.pv', '001tix01084.daca.pv', '001uxm0rf01.daca.pv',
                       '001uxm0rf02.daca.pv', '001uxm0rf03.daca.pv', 'temp_zuz', 'temp_last_1',
                       'temp_last_2', 'temp_last_3', 'temp_last_4', '001fcx00211.pv_avg_00-15',
                       '001fcx00221.pv_avg_00-15', '001fir01307.daca.pv_avg_00-15',
                       '001fir01308.daca.pv_avg_00-15', '001fir01309.daca.pv_avg_00-15',
                       '001fir01310.daca.pv_avg_00-15', '001fir01311.daca.pv_avg_00-15',
                       '001fir01312.daca.pv_avg_00-15', '001fir01315.daca.pv_avg_00-15',
                       '001nir0szr0.daca.pv_avg_00-15', '001fcx00211.pv_avg_15-30',
                       '001fcx00221.pv_avg_15-30', '001fir01307.daca.pv_avg_15-30',
                       '001fir01308.daca.pv_avg_15-30', '001fir01309.daca.pv_avg_15-30',
                       '001fir01310.daca.pv_avg_15-30', '001fir01311.daca.pv_avg_15-30',
                       '001fir01312.daca.pv_avg_15-30', '001fir01315.daca.pv_avg_15-30',
                       '001nir0szr0.daca.pv_avg_15-30', '001fcx00211.pv_avg_30-45',
                       '001fcx00221.pv_avg_30-45', '001fir01307.daca.pv_avg_30-45',
                       '001fir01308.daca.pv_avg_30-45', '001fir01309.daca.pv_avg_30-45',
                       '001fir01310.daca.pv_avg_30-45', '001fir01311.daca.pv_avg_30-45',
                       '001fir01312.daca.pv_avg_30-45', '001fir01315.daca.pv_avg_30-45',
                       '001nir0szr0.daca.pv_avg_30-45', '001fcx00211.pv_avg_45-60',
                       '001fcx00221.pv_avg_45-60', '001fir01308.daca.pv_avg_45-60',
                       '001fir01309.daca.pv_avg_45-60', '001fir01310.daca.pv_avg_45-60',
                       '001fir01311.daca.pv_avg_45-60', '001fir01312.daca.pv_avg_45-60',
                       '001fir01315.daca.pv_avg_45-60', '001nir0szr0.daca.pv_avg_45-60']
                       
    corr_df = new_df[correlated_cols].copy()

    corr_df['temp_zuz'] = corr_df['temp_zuz'].interpolate()
    df = corr_df.dropna()

    df['minute'] = df.index.minute.values
    df['minute'] = np.where(df['minute'] == 0, 60, df['minute'])
    return df
