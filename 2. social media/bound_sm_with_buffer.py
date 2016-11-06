# coding=utf-8
__author__ = 'JHW'

import datetime
import sys
import logging
import os
import pandas as pd
import geopandas as gp
import shapely.geometry as shpgeo
from ast import literal_eval
import numpy as np
from dateutil.parser import parse as date_parse
import json

START_TIME = datetime.datetime.now()


def set_Logger(log_name='log_%s_%s.txt' % (START_TIME.strftime('%Y%m%d'), os.path.basename(sys.argv[0])[:-3]),
               format_log='%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'):
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_name)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(format_log)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def costs(start_time=START_TIME):
    dnow = datetime.datetime.now()
    delta = dnow - start_time
    delta_total_seconds_int = int(delta.total_seconds())
    return 'now = %s, costs = %d days %02d:%02d:%02d = %d seconds' % (dnow.strftime('%Y-%m-%d %H:%M:%S'),
                                                                      delta_total_seconds_int / 3600 / 24,
                                                                      delta_total_seconds_int / 3600 % 24,
                                                                      delta_total_seconds_int / 60 % 60,
                                                                      delta_total_seconds_int % 60,
                                                                      delta_total_seconds_int)


def parse_twitter_ts(ts):
    return date_parse(ts)

def parse_linux_time(ts):
    return datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')


def get_poly_gdf(poly_path):
    gdf_poly = gp.read_file(poly_path)
    return gdf_poly

def get_twitter_gpdf(social_media_path):
    df = pd.read_csv(social_media_path,header=None)
    df.columns = ['smid', 'user', 'ts', 'coor_lon', 'coor_lat', 'coor_type', 'geo_lat', 'geo_lon', 'geo_type', 'recnt', 'src', 'truncated', 'urls', 'text']
    df.drop(['coor_type','geo_type','geo_lat','geo_lon','recnt','truncated','src','urls','text'],inplace=True, axis=1)
    df['geometry'] = df.apply(lambda x: shpgeo.Point(float(x.coor_lon),float(x.coor_lat)) if not np.isnan(x.coor_lon) else x.coor_lon,axis=1)
    df.drop(['coor_lon','coor_lat'], inplace=True, axis=1)
    df = df[~df['geometry'].isnull()]
    print 'df twitter shape:', df.shape
    gpdf = gp.GeoDataFrame(df)
    gpdf.crs = {'init':'epsg:4326'}
    return gpdf


def get_flickr_gpdf(social_media_path):
    col_interest = ['smid', 'dateuploaded', 'nsid', 'username', 'realname', 'path_alias', 'owner_loc', 'comments', 'views', 'lat', 'lon',
                    'loc_accuracy', 'loc_placeid', 'date_taken', 'date_posted', 'date_lastupdate', 'date_takengranularity', 'date_takenunknown']

    flickrs = []
    with open(social_media_path) as f:
        for cnt,line in enumerate(f):
            fl = extract_flickr_line(line)
            if type(fl)==list:
                flickrs.append(fl)
            else:
                print 'extract flickr Error in line:', cnt, fl
    flickr_df = pd.DataFrame(flickrs, columns=col_interest)
    print 'flickr_df shape:', flickr_df.shape
    gpdf = gp.GeoDataFrame(flickr_df)
    gpdf.crs = {'init':'epsg:4326'}
    gpdf['geometry'] = flickr_df.apply(lambda x: shpgeo.Point(float(x.lon), float(x.lat)), axis=1)
    return gpdf


def extract_flickr_line(line):
    data = json.loads(line)
    try:
        photo = data['photo']
        pid = photo['id']
        dateuploaded = parse_linux_time(photo['dateuploaded'])
        nsid = photo['owner']['nsid']
        username = photo['owner']['username']
        realname = photo['owner']['realname']
        path_alias = photo['owner']['path_alias']
        owner_loc = photo['owner']['location']
        # title = photo['title']['_content']
        comments = photo['comments']['_content']
        views = photo['views']
        lat = photo['location']['latitude']
        lon = photo['location']['longitude']
        loc_accuracy = photo['location']['accuracy']
        loc_placeid = photo['location']['place_id'] if 'place_id' in photo['location'] else ''
        date_taken = photo['dates']['taken']
        date_posted = parse_linux_time(photo['dates']['posted'])
        date_lastupdate = parse_linux_time(photo['dates']['lastupdate'])
        date_takengranularity = photo['dates']['takengranularity']
        date_takenunknown = photo['dates']['takenunknown']
        return [pid, dateuploaded, nsid, username, realname, path_alias, owner_loc, comments, views, lat, lon, loc_accuracy, loc_placeid,
                            date_taken, date_posted, date_lastupdate, date_takengranularity, date_takenunknown]
    except Exception as e:
        return str(e)


def main():
    # LOGGER.info('test')
    data_dir = '../data/'
    # place_type = 'museum'
    # place_type = 'nationalpark'
    place_polygons_fns = [
        'place_polys_museum.geojson',
        # 'place_polys_museum_convex.geojson',
        # 'place_polys_museum_convex_50m.geojson',
        # 'place_polys_museum_convex_100m.geojson'
    ]
    fl_dir = u'd:\\★★学习工作\\Life in Maryland\\INFM750,CMSC828E Advanced Data Science\\project\\flickr\\museum_radius\\collected\\'
    tw_dir =  u'd:\\★★学习工作\\Life in Maryland\\INFM750,CMSC828E Advanced Data Science\\project\\twitter\\museums\\'
    sm_data = [
        # ['tw', tw_dir+'completed\\collected\\tweets.txt', '1'],
        # ['tw', tw_dir+'collected\\tweets.txt', '2'],
        ['fl', fl_dir+'flickr_photos_1.txt','1'],
        ['fl', fl_dir+'flickr_photos_2.txt','2'],
        ['fl', fl_dir+'flickr_photos_3.txt','3'],
    ]

    for social_media_type, social_media_path, path_suffix in sm_data:
        # social_media_type, social_media_path, path_suffix = 'twitter','twitter/museums/completed/collected/tweets.txt', '1'
        # social_media_type, social_media_path, path_suffix =  'twitter', 'twitter/museums/collected/tweets.txt', '2'
        print 'getting social media:',social_media_type
        social_media_gpdf = get_twitter_gpdf(social_media_path) if social_media_type=='tw' else get_flickr_gpdf(social_media_path)
        print 'got social media', costs()

        for place_polygons_fn in place_polygons_fns:
            print 'getting polygons of %s' % place_polygons_fn
            place_polygons = get_poly_gdf(data_dir+place_polygons_fn)
            # print place_polygons

            print 'sjoining social media and place polygon'
            joined_gdf = gp.sjoin(social_media_gpdf, place_polygons, how='left')
            social_media_in_place = joined_gdf[~joined_gdf.place.isnull()].copy()
            print 'sjoined social media and place polygon', costs()

            print 'adding fields to social media'
            social_media_in_place.place = social_media_in_place.place.apply(lambda x: x[:-1] if x[-1].isdigit() else x)
            if social_media_type=='tw':
                social_media_in_place.ts = social_media_in_place.ts.apply(parse_twitter_ts)
            social_media_in_place.drop(['index_right'],inplace=True, axis=1)
            print 'added fields', costs()

            sm_output_path = '%ssm#%s_%s#%s.csv' % (data_dir, social_media_type, path_suffix, place_polygons_fn.replace('.geojson',''))
            print 'writing results',sm_output_path
            social_media_in_place.to_csv(sm_output_path)

    return


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    print("start_time:", START_TIME.strftime(TIME_FORMAT))

    # LOGGER = set_Logger()

    main()

    END_TIME = datetime.datetime.now()
    DELTA_TIME = END_TIME - START_TIME
    print ('run time: %s - %s = %s ' % (START_TIME.strftime(TIME_FORMAT), END_TIME.strftime(TIME_FORMAT), DELTA_TIME))
