import pickle

import datetime
import tweepy
import json
import pprint
import time
from retrying import retry
import MySQLdb


def api_connect():
    secret_file = "secret.json"
    secret = open(secret_file, "r")
    file_string = secret.read()
    file_json = json.loads(file_string)
    auth = tweepy.OAuthHandler(file_json['key'], file_json['secret'])
    auth.set_access_token(file_json['token'], file_json['token_secret'])
    return tweepy.API(auth)


def db_connect():
    db = MySQLdb.connect("localhost", "root", "", "lol")
    return db


def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


class TwitterEntityFinder:
    def __init__(self):
        self.api = api_connect()
        self.db = db_connect()
        self.cursor_followers = tweepy.Cursor(self.api.followers, screen_name="LeagueOfLegends").items()

    # Retries with exponential back-off, stops after 1 hour
    @retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_delay=3600000)
    def get_next_follower(self, count):
        print 'getting follower number: ', count
        return next(self.cursor_followers)

    def store_follower(self, follower, cursor):

        user_name = follower.name.encode('ascii', 'ignore')
        description = follower.description.encode('ascii', 'ignore')
        fol_count = follower.followers_count
        fri_count = follower.friends_count
        date_created = str(follower.created_at).encode('ascii', 'ignore')
        tweet_count = follower.statuses_count
        language = follower.lang.encode('ascii', 'ignore')
        if tweet_count > 0 and not follower.protected:
            last_post = str(follower.status.created_at).encode('ascii', 'ignore')
        else:
            last_post = ''
        twitter_id = int(follower.id)
        screen_name = follower.screen_name.encode('ascii', 'ignore')

        sql = "INSERT INTO twitter_entity " \
              "(user_name, screen_name, description, " \
              "followers_count, friends_count, " \
              "date_created, tweet_count, language, last_post, " \
              "twitter_id)" \
              " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        print sql

        try:
            cursor.execute(sql, (
            user_name, screen_name, description, fol_count, fri_count, date_created, tweet_count, language,
            last_post,
            twitter_id))
            self.db.commit()
        except MySQLdb.Error, e:
            print e.args[0], e.args[1]
            # self.save_cursor()
            self.db.rollback()

    def save_cursor(self):
        save_obj = {'cursor': self.cursor_followers}
        print save_obj
        save_object(save_obj, 'cursor_save.pkl')

    def main_loop(self):
        count = 0
        cursor = self.db.cursor()

        while True:
            follower = self.get_next_follower(count)
            count += 1
            print len(self.cursor_followers.current_page)
            print "looking at follower: ", follower.name, " ||| ", follower.description
            print follower
            print "now Storing..."
            self.store_follower(follower, cursor)

            time.sleep(2)
        self.db.close()


a = TwitterEntityFinder()
a.main_loop()
# try:
#     a.main_loop()
#
# except Exception:
#     print "Something bad happened"
#     a.save_cursor()
