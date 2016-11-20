# coding=utf-8
__author__ = 'JHW'

import datetime
import sys
import logging
import os
import csv
import tweepy
import json
import pandas as pd
import glob
import time
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


def work_every_sec(sec=1):
    sec = float(sec)
    stop = sec - time.time() % sec
    if stop>0.20:
        time.sleep(stop)
    else:
        time.sleep(0.20)


def get_all_tweetids(files):
    tweetids = set()
    sum_tweetids = 0
    for fn in files:
        if os.path.getsize(fn)==0:
            continue
        try:
            df = pd.read_csv(fn,header=None,sep='\t')
            df.columns = ['uid','tweetid','timestamp','username']
            new_tids = df.tweetid.values
            sum_tweetids+=len(new_tids)
            tweetids.update(new_tids)
        except Exception as e:
            print fn, e
    return tweetids


def get_exist_tweetids(existid_file):
    if os.path.isfile(existid_file):
        return set([int(line.strip()) for line in open(existid_file).read().splitlines()])
    return set()

def extract_tweets(tweets):
    tweets_extracted = []
    tid_extracted = []
    for tweet in tweets:
        try:
            js = tweet._json
            tid = js['id']
            ts = js['created_at']
            coor = js['coordinates']
            coor_lon, coor_lat, coor_type = '','',''
            if coor:
                coor_lon, coor_lat = coor['coordinates']
                coor_type = js['coordinates']['type']
            geo = js['geo']
            geo_lat, geo_lon, geo_type = '','',''
            if geo:
                geo_lat, geo_lon = js['geo']['coordinates']
                geo_type = js['geo']['type']
            urls = []
            for a in js['entities']['urls']:
                urls.append(a['expanded_url'])
            recnt = js['retweet_count']
            src = js['source']
            text = js['text']
            if text:
                text = text.encode('utf8')
            truncated = js['truncated']
            userid = js['user']['id']
            tweets_extracted.append([tid, userid, ts, coor_lon, coor_lat, coor_type, geo_lat, geo_lon, geo_type, recnt, src, truncated, urls, text])
            tid_extracted.append(tid)
        except Exception as e:
            print e
            print tweet
            print '++++++++++++++++++++++++++++++++++++++++++'


    return tweets_extracted, tid_extracted

def get_tweets_output(apis,chunk_tweetids,js_file,existid_file):
    apis_count = apis.__len__()
    tweets_extracted = []
    tweets_ids = []
    for i,chunk in enumerate(chunk_tweetids):
        api = apis[i % apis_count]
        retry = 0
        while retry<6:
            try:
                tweets = api.statuses_lookup(chunk)
                ts, tids = extract_tweets(tweets)
                tweets_extracted.extend(ts)
                tweets_ids.extend(tids)
                work_every_sec()
                break
            except tweepy.TweepError, e:
                print e
                print chunk
                work_every_sec(sec=60)
                retry+=1

        if (i+1)%100==0:
            with open(js_file,'ab') as fjs:
                csv_fjs = csv.writer(fjs)
                with open(existid_file,'a') as fex:
                    csv_fjs.writerows(tweets_extracted)
                    fex.write('\n'.join([str(tid) for tid in tweets_ids])+'\n')
                    tweets_extracted = []
                    tweets_ids=[]
                    print i, costs()
        # if i>100:
        #     break

def main():
    my_twitter_apps =[['lto3a0tyTbAzIRe9ZewMvmH6c', 'jbwbYSyj9Cn5Uchsvg2HEcFuq9SO4xhMAfXdgCLpRUxJD0QcRS',
      '765385925463568384-yKOYfV7BfRMRrOmytgPxhnV8UmjWTQX', '6yu8frcMhGbl5zqunZMH5XruNPmtuZIMwL9zp42vcQT7G'],
     ['sLjDxkgs8kmJFX1h2LxKNvahr','ukrkakFSenlc1j17OsMTMD5j9RLvnPd9ZSzX1GD8tjuygo9L52',
      '765385925463568384-9AB2AJeI7rhYhxmjmGmBTMXoxFpm3G5','LLqO1R1QkYvawS9rY9uVtBN8uer5TP23Br1ZIc33iYYb8'],
     ['mJHTG5OyYbHPHZspZEAvbVhq9','5wlMHItFaoy5UkaDK9c2c7ICfRY35QffOhL9eMqYOfvVJA2J49',
      '765385925463568384-TLoWk8C3n6bLXHrAWYkqKc3ObhbGVAc','B5r4SQVC2d8oXwpt7VC2b6dc3TbQtp7CbX3k28aHCnIxa'],
     ['NoEY966cyOzQ7XYyCmvzx5dJq','v4h5mQXlqV2h7ojOYTvuvniLb5rmlSnqVNNjvi8dWkxQl43f6g',
      '765385925463568384-svWRLCnyNdZQM12gfy6UVSaTnJ5gs5N','DdvWJ1sTWxHBvzIlz2NUM24cIZ40uyj1mK5oYnr3hbIFV'],
     ['l77wvCDSocLi8zIYzF58ILw2p','ViKOeOqdsMQbfMewzQxYCnItX1MAwYfKoig9ou9l72MzNw74Xw',
      '765385925463568384-j0QukAX6Rc89rmw5Q60sOEl3NuZcVWN', 'xD7JX1cmIRHa95TDQ6OZxGVry2fXzAUKpU2ROAKJ0514u']]

    apis = []
    for ckey, csecret, atoken, asecret in my_twitter_apps:
        auth = tweepy.OAuthHandler(ckey, csecret)
        auth.set_access_token(atoken, asecret)
        apis.append(tweepy.API(auth))
    print 'initialed apis'

    dir_path = tw_np_dir
    dir_tweet = tw_np_tweet_dir
    mkdir(dir_path)
    mkdir(dir_tweet)
    js_file = dir_tweet + 'tweets.txt'
    existid_file = dir_tweet+ 'existid.txt'

    tweets_list_files = glob.glob(dir_path+'*.*')
    print 'tweets_list files:', len(tweets_list_files)

    tweetids =  get_all_tweetids(tweets_list_files)
    print 'total tweets:', len(tweetids)

    exist_tweetids = get_exist_tweetids(existid_file)
    print 'exist tweetids:', len(exist_tweetids)

    to_api_tweetids = list(set(tweetids) - set(exist_tweetids))
    print 'tweetids to be collected:', len(to_api_tweetids)

    chunk_size = 100
    chunk_tweetids = [to_api_tweetids[i:i + chunk_size] for i in xrange(0, len(tweetids), chunk_size)]
    print 'total requests:', len(chunk_tweetids), costs()

    print 'collecting tweets'
    get_tweets_output(apis, chunk_tweetids, js_file, existid_file)

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
