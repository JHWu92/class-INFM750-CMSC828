# coding: utf-8

import pandas as pd
import numpy as np


def clean_gt_np(np_raw, np_clean, gt_col):
    df = pd.read_csv(np_raw)
    df.dropna(how='all', inplace=True)
    df['place'] = df['place'].fillna(method='ffill')
    df.drop(u'Unnamed: 14', axis=1, inplace=True)
    clean_df = pd.melt(df, id_vars=['place', 'Year'], var_name='month', value_name=gt_col)
    clean_df.Year = clean_df.Year.apply(lambda x: x.replace(',', ''))
    clean_df.gt_visit = clean_df.gt_visit.apply(lambda x: x.replace(',', '') if type(x) == str else x)
    clean_df.place = clean_df.place.apply(lambda x: x.replace(' ', '_'))
    ', '.join(clean_df.month.value_counts().index.tolist())
    standardized_month = {
        'Jan': '01', 'Feb': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06', 'July': '07', 'August': '08',
        'September': '09', 'October': '10', 'November': '11', 'December': '12'
    }
    clean_df.month = clean_df.month.apply(lambda x: standardized_month[x])
    clean_df['ym'] = clean_df.apply(lambda x: '%s_%s' % (x.Year, x.month), axis=1)
    clean_df.dropna(inplace=True)
    clean_df.to_csv(np_clean)


def clean_gt_m(m_raw, m_clean, gt_col):
    df = pd.read_csv(m_raw)
    df = df.apply(lambda x: x.str.strip().replace('-', np.nan))
    df.columns = ['place'] + list(df.columns[1:])
    melt_df = pd.melt(df, id_vars=['place'], var_name='fy', value_name=gt_col)
    melt_df = melt_df[~melt_df.place.str.contains('_FY_Total')]
    melt_df['month'] = melt_df['place'].apply(lambda x: x.rsplit('_', 1)[1])
    melt_df['place'] = melt_df['place'].apply(lambda x: x.rsplit('_', 1)[0].strip())
    melt_df.gt_visit = melt_df.gt_visit.apply(lambda x: float(x.replace(',', '')) if type(x) == str else x)
    mn2int = {'April': 4, 'May': 5, 'June': 6, 'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11,
              'December': 12, 'January': 1, 'February': 2, 'March': 3}

    def get_yr_mn(x):
        mn = mn2int[x.month]
        fy = x.fy[2:].split('_')
        yr = '20%s' % fy[0 if mn > 3 else 1]
        return '%s_%02d' % (yr, mn)

    melt_df['ym'] = melt_df.apply(get_yr_mn, axis=1)
    melt_df[['place', 'ym', 'gt_visit']].dropna().to_csv(m_clean)


def clean():
    root_data_dir = '../data'
    gt_col = 'gt_visit'

    m_raw = root_data_dir + '/place_m_statistic_raw.csv'
    m_clean = root_data_dir + '/place_m_statistic_clean.csv'
    clean_gt_m(m_raw, m_clean, gt_col)

    np_raw = root_data_dir + '/place_np_statisic_raw.csv'
    np_clean = root_data_dir + '/place_np_statisic_clean.csv'
    clean_gt_np(np_raw, np_clean, gt_col)


if __name__ == '__main__':
    clean()