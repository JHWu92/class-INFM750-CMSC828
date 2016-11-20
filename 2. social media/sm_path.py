tw_np_dir = '../data/social_media_raw/tw/np/'
tw_np_tweet_dir = tw_np_dir + 'tweets/'
tw_museum_dir = '../data/social_media_raw/tw/museum/'


tw_np_csv = '../data/place_polys_np.csv'
def mkdir(ddir):
    import os
    if not os.path.exists(ddir):
        os.makedirs(ddir)