import datetime
import twitter_scrap
import sys
import os
def mkdir(ddir):
    if not os.path.exists(ddir):
        os.makedirs(ddir)


def main(pidx):
    
    import geopandas as gp
    PLACE_POLYS_NP = '../data/place_polys_np.geojson'
    place_gpdf = gp.read_file(PLACE_POLYS_NP)
    radius = place_gpdf['radius+1km'].apply(lambda x: '{}km'.format(int(x/1000)+1)).values
    cntr = place_gpdf.cntr.apply(eval).apply(lambda x: [x[1], x[0]])
    place = place_gpdf['place##cnt'].values
    places = zip(place, cntr, radius, [datetime.datetime(2099,1,1)]*len(place))

    ddir = '../data/social_media_raw/tw/np/'
    mkdir(ddir)
    place = [places[int(pidx)]]
    twitter_scrap.main(place, ddir)

if __name__ == '__main__':
    main(sys.argv[1])