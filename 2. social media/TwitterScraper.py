import datetime
import json
import csv
import logging
import urllib2
import random
import time

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logging.basicConfig(filename='err.log', level=logging.ERROR)
ua = UserAgent()
headers_list = [ua.chrome, ua.google, ua['google chrome'], ua.firefox, ua.ff,'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:32.0) Gecko/20100101 Firefox/32.0']


class Scraper:
    def __init__(self, topics, no_tweets=float('inf'), lang='', begin_date='', end_date='', authors='', recipients='',
                 near='', within=1, filename=''):
        self.topics = self.parse_topics(topics)
        self.no_tweets = no_tweets
        self.lang = lang
        self.begin_date = begin_date
        self.end_date = end_date
        self.authors = self.parse_authors(authors)
        self.recipients = self.parse_recipients(recipients)
        self.filename = filename
        self.first_tweet_id = 0
        self.last_tweet_id = 0
        self.last_6_tweet_id = []
        self.last_timestamp = ''
        self.collected_tweets = 0
        self.location = self.parse_location(near, within)
        self.min_position = -1
        self.html = ''
        if self.filename:
            self.writer = csv.writer(open(self.filename, 'wb'), delimiter="\t")

    def parse_topics(*topics):
        if type(topics[1]) is str:
            topics_string = topics[1]
        elif type(topics[1]) is list:
            topics_string = ' '.join(topics[1])
        topics_string = topics_string.replace(' ', '%20')
        return topics_string

    def parse_authors(*authors):
        if authors[1]:
            if type(authors[1]) is str:
                authors_string = authors[1]
            elif type(authors[1]) is list:
                authors_string = "%20OR%20from%3A".join(authors[1])
            return authors_string

    def parse_recipients(*recipients):
        if recipients[1]:
            if type(recipients[1]) is str:
                recipients_string = recipients[1]
            elif type(recipients[1]) is list:
                recipients_string = "%20OR%20to%3A".join(recipients[1])
            return recipients_string

    def parse_location(self, location, within):
        if location:
            if type(location) is str:
                location_string = 'near%3A"' + location + '"%20within%3A' + within
            elif type(location) is list:
                location_string = '"geocode%3A' + str(location[0]) + '%2C' + str(location[1]) + '%2C' + within
            return location_string

    def is_first_iteration(self):
        return True if self.min_position == -1 else False

    def continue_scraping(self, tweets):
        if (self.collected_tweets < self.no_tweets) and len(tweets) > 0:
            return True
        else:
            print self.collected_tweets < self.no_tweets, 'num of tweets', len(tweets)
            print 'tweets:',tweets
            print self.parse_url()
            print 'html len:', len(self.html)
            with open('empty html.html','w') as f:
                f.write(self.html)
            return False

    def parse_url(self):
        url_1 = "https://twitter.com/search?f=tweets&vertical=default&q="
        url_2 = "https://twitter.com/i/search/timeline?f=tweets&vertical=default&include_available_features=1&include_entities=1&reset_error_state=false&src=typd"
        if self.is_first_iteration():
            url = url_1 + self.topics
        else:
            url = url_2 + "&max_position=%s&q=%s" % (self.min_position, self.topics)
        if self.lang: url += "%20lang%3A" + self.lang
        if self.begin_date: url += "%20since%3A" + self.begin_date
        if self.end_date: url += "%20until%3A" + self.end_date
        if self.authors: url += "%20from%3A" + self.authors
        if self.recipients: url += "%20to%3A" + self.recipients
        if self.location: url += '%20' + self.location
        # print url
        return url

    def scrape_tweets(self):
        url = self.parse_url()
        headers = {'User-Agent': random.choice(headers_list)}
        req = urllib2.Request(url, headers=headers)
        tweets = []
        error = True
        try:
            response = urllib2.urlopen(req,timeout=10).read()
            if self.is_first_iteration():
                html = response
            else:
                response_json = json.loads(response)
                html = response_json['items_html']
            # print html
            self.html = html
            soup = BeautifulSoup(html, "lxml")
            tweets = soup.find_all('li', 'js-stream-item')
            if tweets:
                self.last_tweet_id = tweets[-1]['data-item-id']
                last_6_tweets = tweets[-6:]
                self.last_6_tweet_id = [t['data-item-id'] for t in last_6_tweets]
                self.first_tweet_id = tweets[0]['data-item-id']
                if self.is_first_iteration():
                    self.min_position = "TWEET-%s-%s" % (self.last_tweet_id, self.first_tweet_id)
                else:
                    minp_splitted = response_json['min_position'].split('-')
                    minp_splitted[1] = self.last_tweet_id
                    self.min_position = "-".join(minp_splitted)
            error=False
        except urllib2.HTTPError, e:
            logging.error('HTTPError = ' + str(e.code))
            print 'HTTPError = ' + str(e.code)
        except urllib2.URLError, e:
            logging.error('URLError = ' + str(e.reason))
            print 'URLError = ' + str(e.reason) + self.begin_date + '~'+self.end_date
        except Exception:
            import traceback
            logging.error('generic exception: ' + traceback.format_exc())
            print 'generic exception: ' + traceback.format_exc()

        return tweets,error



    def extract_data_from_tweet(self, tweet):
        tweet_user = tweet.find('span', 'username')
        if tweet_user:
            tweet_user= tweet_user.text
        tweet_fullname = tweet.find('strong', 'fullname')
        if tweet_fullname:
            tweet_fullname = tweet_fullname.text.encode('utf8')
        tweet_id = tweet['data-item-id']
        timestamp = tweet.find('a', 'tweet-timestamp')['title']
        self.last_timestamp = timestamp
        post = [tweet_user, tweet_id, timestamp, tweet_fullname]
        return post

    def write(self, post):
        if self.filename:
            self.writer.writerow(post)
        else:
            print post

    def scrape(self):
        tweets = [-1]
        print "collecting %s number of Tweets on the topics: %s" % (self.no_tweets, self.topics)
        outer_retry = 0
        while outer_retry<6:
            while self.continue_scraping(tweets):
                if outer_retry>0 and tweets != [-1]:
                    print 'outer retried %d succeeded' % outer_retry
                    outer_retry=0
                retry = 0
                while retry<6:
                    tweets,error = self.scrape_tweets()
                    if not error:
                        break
                    print 'retry =', retry
                    retry+=1
                    time.sleep(20)
                if retry<6 and retry>0:
                    print 'retry =', retry, 'succeeded'
                for tweet in tweets:
                    self.collected_tweets += 1
                    post = self.extract_data_from_tweet(tweet)
                    self.write(post)
                if self.collected_tweets%3000<20:
                    print 'collected tweets:',self.collected_tweets, datetime.datetime.now()
                # time.sleep(1.5)

            outer_retry+=1
            last_6_tweets_id_len = len(self.last_6_tweet_id)
            if last_6_tweets_id_len>0:
                idx_for_last_6_tweet = outer_retry if outer_retry<last_6_tweets_id_len else last_6_tweets_id_len-1
                print 'tweets is null, retry:',outer_retry, 'last tweet id switch from %s to %s' % (self.last_tweet_id, self.last_6_tweet_id[idx_for_last_6_tweet])
                self.last_tweet_id = self.last_6_tweet_id[idx_for_last_6_tweet]
                minp_splitted = self.min_position.split('-')
                minp_splitted[1] = self.last_tweet_id
                self.min_position = "-".join(minp_splitted)
            else:
                print 'tweets and last 6 tweets are null, retry:', outer_retry
            tweets=[-1]
            print 'time sleep 10'
            time.sleep(10)
        print 'returning scrape'
        return self.last_timestamp


