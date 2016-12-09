# coding=utf-8
DATA_DIR = '../data/'
bfrs = ['','_5m','_10m', '_50m', '_100m']
pbs = ['place_polys_'+p+bfr for p in ['m','np'] for bfr in bfrs]
print pbs
# place_choices = [
#     'place_polys_museum','place_polys_museum_convex','place_polys_museum_convex_5m','place_polys_museum_convex_10m',
#     'place_polys_museum_convex_50m','place_polys_museum_convex_100m',
#     'place_polys_np','place_polys_np_5m','place_polys_np_10m','place_polys_np_50m','place_polys_np_100m',
# ]
bounded_tw_paths = [DATA_DIR+'sm#tw_{}#{}.csv'.format((i+1), pb)for i in range(2) for pb in pbs ]
bounded_fl_paths = [DATA_DIR+'sm#fl_{}#{}.csv'.format((i+1), pb)for i in range(3) for pb in pbs ]

import os
bounded_tw_paths = [x for x in bounded_tw_paths if os.path.isfile(x)]
bounded_fl_paths = [x for x in bounded_fl_paths if os.path.isfile(x)]

import pandas as pd
path_df = pd.DataFrame(bounded_fl_paths+bounded_tw_paths,columns=['path'])
path_df['fn']=path_df.path.apply(lambda x: x.rsplit('/',1)[1].replace('.csv',''))
path_df['sm']=path_df.fn.apply(lambda x: x.split('#')[1].split('_')[0])
path_df['bfr']=path_df.fn.apply(lambda x: x.split('#')[2])
print path_df

dfs_sm = {}
for bfr_smtype, grp in path_df.groupby(['bfr','sm']):
    df_concat = []
    for path in grp.path.values:
        df = pd.read_csv(path,index_col=0)
        df_concat.append(df)
    df_concat = pd.concat(df_concat)
    dfs_sm[bfr_smtype] = df_concat

def simplify_sm(dfs_sm):
    from dateutil.parser import parse as date_parse
    def get_yr_mn_dy(x):
        dt = date_parse(x)
        return '%s_%02d_%02d' %(dt.year, int(dt.month),int(dt.day))
    def clean_place(x):
        x = x.split('##')[0]
        x = x[:-1] if x[-1].isdigit() else x
        return x.replace(' ','_')
    dfs_sm_simplified = {}
    for (bfr, smtype), df_sm in dfs_sm.items():
        ts_col = {'tw':'ts', 'fl':'date_taken'}[smtype]
        keep_cols = {'tw':['smid','user','place','ymd','ym'],'fl':['smid','nsid', 'place', 'ymd','ym']}[smtype]
        df = df_sm.copy()
        df['ymd'] = df[ts_col].apply(get_yr_mn_dy)
        df['ym'] = df.ymd.apply(lambda x:x[:-3])
        df = df[keep_cols].copy()
        df.columns = ['smid','user','place', 'ymd','ym']
        df.place = df.place.apply(clean_place)
        dfs_sm_simplified[(bfr, smtype)]=df
    return dfs_sm_simplified
dfs_sm_simplified = simplify_sm(dfs_sm)

print dfs_sm_simplified.keys()

month_of_interest_path = '../data/months_of_interest.txt'
MONTHS = pd.read_csv(month_of_interest_path).ym.tolist()
print MONTHS

def agg_month_lvl(dfs_sm, months):
    dfs_sm_mn_lvl = {}
    for (bfr,smtype), df_sm in dfs_sm.items():
        visit_col = '{}_visit'.format(smtype)
        sm_mn_lvl = pd.DataFrame(columns=['place','ym',visit_col])
        for place, gb in df_sm.groupby('place'):
            place_df = gb.copy()
            place_df = place_df.drop_duplicates(['ymd','user'])
            mn_lvl = place_df.groupby('ym').count()['ymd']
            min_month_idx = months.index(mn_lvl.index.min()) if smtype=='tw' else 0
            if min_month_idx<12:
                mn_lvl = mn_lvl.reindex(months[min_month_idx:]).fillna(0)
                mn_lvl = mn_lvl.reset_index()
                mn_lvl.columns = ['ym',visit_col]
                mn_lvl['place'] = place
                sm_mn_lvl = pd.concat([sm_mn_lvl, mn_lvl], ignore_index=True)
#                 print mn_lvl.head()
        dfs_sm_mn_lvl[(bfr,smtype)] = sm_mn_lvl
    return dfs_sm_mn_lvl

dfs_sm_mn_lvl = agg_month_lvl(dfs_sm_simplified,MONTHS)

def output_mn_lvl(dfs_sm_mn_lvl):
    for (bfr,smtype), df_sm_mn_lvl in dfs_sm_mn_lvl.items():
        df_sm_mn_lvl.to_csv('../data/mn_lvl_sm#{}#{}.csv'.format(smtype, bfr))
output_mn_lvl(dfs_sm_mn_lvl)



