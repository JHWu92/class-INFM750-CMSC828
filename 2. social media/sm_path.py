# coding=utf-8
tw_np_dir = '../data/social_media_raw/tw/np'
tw_np_tweet_dir = tw_np_dir + '/tweets'
tw_np_csv = '../data/place_polys_np_tw.csv'

tw_museum_dir = '../data/social_media_raw/tw/museum'
tw_museum_tweet_dir = u'd:\\★★学习工作\\Life in Maryland\\INFM750,CMSC828E Advanced Data Science\\project\\twitter\\museums'

fl_np_geoj = '../data/place_polys_np.geojson'
fl_np_dir = '../data/social_media_raw/flickr/np'
fl_np_info_dir = fl_np_dir + '/info'

fl_museum_info_dir = u'd:\\★★学习工作\\Life in Maryland\\INFM750,CMSC828E Advanced Data Science\\project\\flickr\\museum_radius\\collected'


def mkdir(ddir):
    import os
    if not os.path.exists(ddir):
        os.makedirs(ddir)