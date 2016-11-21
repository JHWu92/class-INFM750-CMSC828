# coding=utf-8
__author__ = 'JHW'

import datetime
import sys
import logging
import os
import glob
import sys, os
sys.path.insert(0, os.path.abspath('../'))
from utils.geofunc import grid_area, haversine

import json
import geopandas as gp
from sm_path import *


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


import flickrapi
import time
def get_flickr_apis():
    authns = [['a521d5d3c70356edc08a1b560d839879','3096c5cc9e7a4c73'],
          ['008e990772c519e20b38a36afa024fba','ad1126a3684db9e0'],
          ['86fd7c017098976abc4412ef464e5dce','7cdf9f5e6ac15312'],
          ['0b3989474fd4cf0a185eb0e72a4aa733','717b767e26785875'],
          ['d188385b0e69fcdea63ca7d9611123b5','6357734eda8665f6']]
    return [flickrapi.FlickrAPI(api_key, secret_api_key) for api_key, secret_api_key in authns]


def work_every_sec(sec=1):
    sec = float(sec)
    stop = sec - time.time() % sec
    if stop>0.05:
        time.sleep(stop)
    else:
        time.sleep(0.05)


CNT_REQUEST = 0
def get_api(flickr_apis):
    global CNT_REQUEST
    flickr = flickr_apis[CNT_REQUEST % len(flickr_apis)]
    CNT_REQUEST +=1
    work_every_sec(0.2)
    return flickr


def get_info_list(p_list):
    stat = p_list['stat']
    photos = p_list['photos']
    total = photos['total']
    perpage = photos[u'perpage']
    page = photos[u'page']
    pages = photos[u'pages']
    photo = photos['photo']
    photo_cnt = len(photo)
    return photo_cnt, stat, total, perpage, page, pages

def save_flickr(file_name, parameters, photo_list,flickr_apis):
    result_list = [json.dumps(photo_list)]
    photo_cnt, stat, total, perpage, page, pages = get_info_list(photo_list)
    max_page = pages
    while page<max_page:
        page+=1
        # print 'try page=',page
        retry = 0
        while retry<6:
            flickr = get_api(flickr_apis)
            new_photo_list = flickr.photos.search(page=page, min_taken_date=parameters[0], max_taken_date=parameters[1],
                                              lon=str(parameters[2]), lat=str(parameters[3]),
                                                  radius=parameters[4],format='parsed-json')
            photo_cnt, stat, total, perpage, page, pages = get_info_list(new_photo_list)
            if pages>max_page: max_page=pages

            if photo_cnt>0:
                break
            retry +=1
        # print 'finish page=', page
        result_list.append(json.dumps(new_photo_list))
    with open(file_name, 'wb') as f:
        for l in result_list:
            f.write(l+'\n')
    print 'finish file:', file_name, costs()
def mkdir(ddir):
    if not os.path.exists(ddir):
        os.makedirs(ddir)

def get_max_dis_from_center_to_ext(centr,ext_coords):
    lon1, lat1 = centr
    return max([haversine(lon1,lat1, lon2,lat2) for lon2, lat2 in ext_coords])

def get_cntr_radius(poly):
    cntr = poly.centroid.coords[0]
    ext_coords = poly.exterior.coords
    radius = get_max_dis_from_center_to_ext(cntr, ext_coords)
    return cntr, radius, ext_coords

def get_place_large(place_gpdf_large):
    import shapely.geometry as shpgeo
    l = zip(place_gpdf_large['place##cnt'].values,
            place_gpdf_large.geometry.values,
            place_gpdf_large['radius+1km'].values)
    place_large = []
    for place, poly, radius in l:
        cnt = 0
        ngrid = int(radius/32000) +2
        w,s,e,n = poly.bounds
        gridded = grid_area((s,w),(n,e), ngrid=ngrid)
        desire_boxes = []
        for (s,w),(n,e) in gridded:
            box = shpgeo.box(w,s,e,n)
            if box.intersects(poly):
                [lon,lat], radius, ext_coords = get_cntr_radius(box)
                sub_place = place + '[%d]' % cnt
                cnt+=1
                desire_boxes.append((sub_place, [lat,lon], '{}km'.format(int(radius/1000)+1)))
        place_large.extend(desire_boxes)
    return place_large


def get_places(place_gpdf):
    place_gpdf_small = place_gpdf[place_gpdf['radius+1km']<=32000]

    places_small = zip(place_gpdf_small['place##cnt'].values,
                       place_gpdf_small.cntr.apply(eval).apply(lambda x: (x[1],x[0])).values,
                       place_gpdf_small['radius+1km'].apply(lambda x: '{}km'.format(int(x/1000)+1)).values)
    place_gpdf_large = place_gpdf[place_gpdf['radius+1km']>32000]
    place_large = get_place_large(place_gpdf_large)
    places = places_small+place_large
    return places

def main():
    # LOGGER.info('test')
    place_polys_np = fl_np_geoj
    place_gpdf = gp.read_file(place_polys_np)
    places = get_places(place_gpdf)

    flickr_apis = get_flickr_apis()
    ddir = fl_np_dir
    mkdir(ddir)
    crawled_places = set([f.rsplit('_',2)[0].split('\\')[1] for f in glob.glob(ddir+'*.*')])
    print 'crawled places len =',crawled_places.__len__()

    cnt_skip = 0
    for place, [lat,lon], radius in places:
        if place in crawled_places:
            cnt_skip+=1
            print 'skip', cnt_skip, place
            continue
        dates = [datetime.datetime(2014,1,1), datetime.datetime(2016,9,1)]
        print '\n==========================='
        print place, lon, lat, radius
        while len(dates)>0:
            date_end = dates.pop()
            date_end_str = str(date_end)
            date_start = dates.pop()
            date_start_str = str(date_start)
            flickr = get_api(flickr_apis)
            photo_list = flickr.photos.search(min_taken_date=date_start_str, max_taken_date=date_end_str,
                                          lon=str(lon), lat=str(lat), radius=radius,format='parsed-json')
            photo_cnt, stat, total, perpage, page, pages = get_info_list(photo_list)
            # print date_start_str, date_end_str
            # print photo_cnt, stat, total, perpage, page, pages
            if int(total)>3500:
                mid_date = date_start+(date_end-date_start)/2
                mid_date = mid_date.replace(minute=0,second=0)
                dates.extend([date_start,mid_date, mid_date, date_end])
            elif int(total)>400000 and (date_end-date_start).days<=2:
                LOGGER.info('%s_%s_%s.txt failed' % (place, date_start_str,date_end_str))
                break
            else:
                parameters = [date_start_str, date_end_str, lon, lat, radius]
                file_name = ddir+'%s_%s_%s.txt' % (place, date_start_str,date_end_str)
                file_name = file_name.replace(':','-')
                print 'total < 3500, go to save flickr for every following pages',date_start_str, date_end_str
                save_flickr(file_name,parameters,photo_list,flickr_apis)
            # print dates
        # break

    return


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    print("start_time:", START_TIME.strftime(TIME_FORMAT))

    LOGGER = set_Logger()

    main()

    END_TIME = datetime.datetime.now()
    DELTA_TIME = END_TIME - START_TIME
    print ('run time: %s - %s = %s ' % (START_TIME.strftime(TIME_FORMAT), END_TIME.strftime(TIME_FORMAT), DELTA_TIME))
