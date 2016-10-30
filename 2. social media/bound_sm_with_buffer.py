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
def get_poly_gdf(poly_path, buffer_ratio=None):
    df_polygon = pd.read_csv(poly_path, sep='\t', header=None, names=['place', 'cntr', 'radius', 'geometry'])
    df_polygon.place = df_polygon.place.apply(lambda x: x.rsplit('_', 3)[0])
    df_polygon.geometry = df_polygon.geometry.apply(lambda x: shpgeo.Polygon(literal_eval(x)))
    gdf_poly = gp.GeoDataFrame(df_polygon)
    if buffer_ratio:
        pass
    gdf_poly.drop(['cntr','radius'],inplace=True, axis=1)
    return gdf_poly

def get_twitter(social_media_path):
    df = pd.read_csv(social_media_path,header=None)
    df.columns = ['smid', 'user', 'ts', 'coor_lon', 'coor_lat', 'coor_type', 'geo_lat', 'geo_lon', 'geo_type', 'recnt', 'src', 'truncated', 'urls', 'text']
    df.drop(['coor_type','geo_type','geo_lat','geo_lon','recnt','truncated','src','urls','text'],inplace=True, axis=1)
    df['geometry'] = df.apply(lambda x: shpgeo.Point(float(x.coor_lon),float(x.coor_lat)) if not np.isnan(x.coor_lon) else x.coor_lon,axis=1)
    df.drop(['coor_lon','coor_lat'], inplace=True, axis=1)
    df = df[~df['geometry'].isnull()]
    print 'df twitter shape:', df.shape
    return gp.GeoDataFrame(df)


def parse_twitter_ts(ts):
    return date_parse(ts)
import json
def extract_flickr(js_str):
    data = json.loads(js_str)
    photo = data['photo']
    pid = photo['id']
    try:
        ts = date_taken = photo['dates']['taken']
    except Exception as e:
        print pid,e

def get_flickr(social_media_path):
    return

def main():
    # LOGGER.info('test')
    place_type = 'museum'
    # place_type = 'nationalpark'
    place_polygons_path = '%s_polygon_osm.tsv' % place_type

    buffer_ratio = 1
    print 'getting polygons of %s with buffer ratio=' % place_type ,buffer_ratio, costs()
    place_polygons = get_poly_gdf(place_polygons_path)

    # social_media_type, social_media_path, path_suffix = 'twitter','twitter/museums/completed/collected/tweets.txt', '1'
    social_media_type, social_media_path, path_suffix =  'twitter', 'twitter/museums/collected/tweets.txt', '2'

    print 'getting social media:',social_media_type, costs()
    social_media_gpdf = get_twitter(social_media_path) if social_media_type=='twitter' else get_flickr(social_media_path)

    print 'sjoining social media and place polygon', costs()
    joined_gdf = gp.sjoin(social_media_gpdf, place_polygons, how='left')
    social_media_in_place = joined_gdf[~joined_gdf.place.isnull()].copy()

    print 'adding fields to social media', costs()
    social_media_in_place.place = social_media_in_place.place.apply(lambda x: x[:-1] if x[-1].isdigit() else x)
    if social_media_type=='twitter':
        social_media_in_place.ts = social_media_in_place.ts.apply(parse_twitter_ts)
    social_media_in_place['ymd'] = social_media_in_place.ts.apply(lambda x: '%s_%02d_%02d' %(x.year, int(x.month),int(x.day)))
    social_media_in_place['ym'] = social_media_in_place.ymd.apply(lambda x: x[:-3])
    social_media_in_place.drop(['index_right'],inplace=True, axis=1)

    print 'writing results', costs()
    sm_output_path = '%s\\%s%s_buffer=%d.csv' % (place_type, social_media_type, path_suffix, buffer_ratio)
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
