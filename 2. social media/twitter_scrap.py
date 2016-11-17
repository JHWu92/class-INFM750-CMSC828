# coding=utf-8
__author__ = 'JHW'

import datetime
import sys
import logging
import os
import time
from dateutil.relativedelta import relativedelta
import TwitterScraper
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


def get_dates(divided_6mns=True):
    date = datetime.datetime(2014,1,1)
    date_until = datetime.datetime(2016,9,1)
    if not divided_6mns:
        return [date, date_until]
        pass
    dates = []
    while date < date_until:
        dates.append(date)
        date+=relativedelta(months=+6)
        if date>date_until:
            date = date_until
        dates.append(date)
        # print date
    return dates

def mkdir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def file_exist(file_path):
    if not os.path.isfile(file_path): return False
    elif os.path.getsize(file_path)<100*1024.0: return False
    return True

def main(places, dir, dates=[], given_dates=False):
    LOGGER = set_Logger()
    mkdir(dir)
    for place, latlon, radius, resume_date in places:
        print place
        if not given_dates: dates = get_dates(False)
        while len(dates)>0:
            print 'while len date', len(dates)
            date_end = dates.pop()
            date_start = dates.pop()

            # resume to last date of tweet crawled
            if date_start>= resume_date: continue
            elif date_start< resume_date and date_end>resume_date: date_end=resume_date


            str_date_end = str(date_end)[:10]
            str_date_start = str(date_start)[:10]

            if str_date_end == str_date_start:
                continue

            path_outfile = dir+'%s_%s_%s.csv' % ( place, str_date_start, str_date_end)
            if file_exist(path_outfile):
                print path_outfile,'exists, pass'
                continue

            try:
                scraper = TwitterScraper.Scraper('', begin_date=str_date_start, end_date=str_date_end,
                                     near=latlon, within=radius, filename = path_outfile)
                print 'scarping %s' % path_outfile, costs()
                str_last_timestamp = scraper.scrape()
            except Exception as e:
                LOGGER.info(str(e)+'\t'+path_outfile)
                print str(e)+'\t'+path_outfile
                raise e
                continue

            if str_last_timestamp:
                dt = datetime.datetime.strptime(str_last_timestamp,'%H:%M %p - %d %b %Y')
                if not dt<date_start:
                    dates.append(date_start)
                    dates.append(dt)
                else:
                    print 'finished one round'
            else:
                print 'no last time stamp, should finished'
                LOGGER.info('no last time stamp, should finished'+'\t'+path_outfile)
            print 'sleep for 40s'
            time.sleep(40)
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
