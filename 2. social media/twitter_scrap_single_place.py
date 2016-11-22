import datetime
import twitter_scrap
import sys
import os
from sm_path import *



def main(pidx):
    
    import pandas as pd
    import datetime
    place_df = pd.read_csv(tw_np_csv, index_col=0)
    radius = place_df['radius'].apply(lambda x: '{}km'.format(int(x/1000)+1)).values
    cntr = place_df.cntr.apply(eval).apply(lambda x: [x[1], x[0]])
    place = place_df['place'].values
    date_until = [datetime.datetime.strptime(x,'%Y-%m-%d') for x in place_df['date_until'].values]
    places = zip(place, cntr, radius, date_until)
    print len(places)
    ddir = tw_np_dir
    mkdir(ddir)
    place = [places[int(pidx)]]
    twitter_scrap.main(place, ddir)

if __name__ == '__main__':
    main(sys.argv[1])