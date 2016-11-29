# coding=utf-8
__author__ = 'JHW'

import datetime
import sys
import logging
import os

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
    # work_every_sec(0.2)
    return flickr


def get_photo_ids(museum_lists_file):
    photo_ids = []
    no_photo_list = []
    for mf in museum_lists_file:
        # print mf
        with open(mf) as f:
            for i, line in enumerate(f):
                data = json.loads(line)
                photo = data['photos']['photo']
                # print data
                if not photo:
                    no_photo_list.append((mf, i))
                    continue
                df = pd.DataFrame(photo)
                ids = list(df.id)
                photo_ids+=ids
                # break
        # break
    photo_ids = [int(x) for x in photo_ids]
    return photo_ids, no_photo_list


def save_no_photo_list(no_photo_list):
    with open(NO_PHOTO_FILE, 'w') as f:
        for mf, i in no_photo_list:
            f.write('%s\t%s\n' % (mf,i))


def get_exist_ids():
    if os.path.isfile(EXISTID_FILE):
        return set([int(line.strip()) for line in open(EXISTID_FILE).read().splitlines()])
    return set()


def output_photo(p_list, pid_list):
    with open(TO_COLLECT_IDS_FILE,'ab') as f:
        for p in p_list:
            f.write(json.dumps(p)+'\n')
    with open(EXISTID_FILE, 'ab') as f:
        f.write('\n'.join([str(pid) for pid in pid_list])+'\n')

def get_photo_output(to_collect_ids,flickr_apis):
    p_list = []
    pid_list = []
    for i, pid in enumerate(to_collect_ids):
        flickr = flickr_apis[i%5]
        retry = 0
        while retry<6:
            try:
                p = flickr.photos.getInfo(photo_id=pid, format='parsed-json')
                p_list.append(p)
                pid_list.append(p['photo']['id'])
                # print i, pid, p['photo']['id']
                break
            except Exception as e:
                info = 'failed:%s\t%s\t%s\%s' % (retry, i, pid, e)
                LOGGER.info(info)
                print info
                retry+=1

        if (i+1) % 500==0:
            output_photo(p_list, pid_list)
            pid_list = []
            p_list=[]
            print 'out put photos, i=', i, costs()
    if len(p_list)>0:
        output_photo(p_list, pid_list)
        print 'output the last photos', costs()

    return

import glob
import json
import pandas as pd
from sm_path import *
DIR = fl_np_dir
OUTPUT_DIR = fl_np_info_dir
NO_PHOTO_FILE = OUTPUT_DIR + '/no_photo_list.tsv'
EXISTID_FILE = OUTPUT_DIR + '/exstid.txt'
TO_COLLECT_IDS_FILE = OUTPUT_DIR+'/flickr_photos.txt'

def main():
    # LOGGER.info('test')
    mkdir(DIR)
    mkdir(OUTPUT_DIR)
    flickr_apis = get_flickr_apis()
    glob_pattern = DIR + '/*.*'
    museum_lists_file = glob.glob(glob_pattern)
    print 'len of museum lists files:', len(museum_lists_file)

    total_photo_ids, no_photo_list = get_photo_ids(museum_lists_file)

    save_no_photo_list(no_photo_list)
    print 'len of no photo list:', len(no_photo_list)

    print 'len of list photo ids:', len(total_photo_ids),
    total_photo_ids = set(total_photo_ids)
    print 'len of set photo ids:', len(total_photo_ids)


    existids = get_exist_ids()
    print 'len of existids:', len(existids)

    # print total_photo_ids
    # print existids

    to_collect_ids = list(total_photo_ids-existids)
    print 'len of ids to be collected:', len(to_collect_ids)

    print 'collecting photos'
    get_photo_output(to_collect_ids, flickr_apis)
    print 'finished collecting'
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
