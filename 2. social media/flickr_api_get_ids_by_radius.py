# coding=utf-8
__author__ = 'JHW'

import datetime
import sys
import logging
import os
import glob

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

CNT_REQUEST = 0

def work_every_sec(sec=1):
    sec = float(sec)
    stop = sec - time.time() % sec
    if stop>0.05:
        time.sleep(stop)
    else:
        time.sleep(0.05)


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
import json

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


import geopandas as gp
PLACE_POLYS_NP = '../data/place_polys_np.geojson'
place_gpdf = gp.read_file(PLACE_POLYS_NP)
place_gpdf_small = place_gpdf[place_gpdf['radius+1km']<=32000]
radius = place_gpdf_small['radius+1km'].apply(lambda x: '{}km'.format(int(x/1000)+1)).values
cntr = place_gpdf_small.cntr.apply(eval).apply(lambda x: (x[1],x[0])).values
place = place_gpdf_small['place##cnt'].values
places_small = zip(place, cntr, radius)

def main():
    # LOGGER.info('test')
    flickr_apis = get_flickr_apis()
    ddir = '../data/social_media_raw/flickr/np/'
    mkdir(ddir)
    crawled_places = set([f.rsplit('_',2)[0].split('\\')[1] for f in glob.glob(ddir+'*.*')])
    print 'crawled places len =',crawled_places.__len__()
    cnt_skip = 0
    for place, [lat,lon], radius in places_small:
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
