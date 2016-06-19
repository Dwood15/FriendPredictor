import pickle
import datetime
import tools
import tweepy
import pprint
import time
from retrying import retry
import MySQLdb


class TwitterEntityFinder:
    def __init__(self):
        self.api = tools.api_connect()
        self.db = tools.db_connect()
        self.cursor_followers = tweepy.Cursor(self.api.followers, screen_name="LeagueOfLegends").items()

    # Retries with exponential back-off, stops after 1 hour
    @retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_delay=3600000)
    def get_next_follower(self, count):
        print 'getting follower number: ', count
        return next(self.cursor_followers)

    def store_follower(self, follower, cursor):
        # Pull storage values out of follower object
        user_name = follower.name.encode('ascii', 'ignore')
        description = follower.description.encode('ascii', 'ignore')
        fol_count = follower.followers_count
        fri_count = follower.friends_count
        date_created = str(follower.created_at).encode('ascii', 'ignore')
        tweet_count = follower.statuses_count
        language = follower.lang.encode('ascii', 'ignore')
        if hasattr(follower, 'status') and hasattr(follower.status, 'created_at'):
            last_post = str(follower.status.created_at).encode('ascii', 'ignore')
        else:
            last_post = ''
        twitter_id = int(follower.id)
        screen_name = follower.screen_name.encode('ascii', 'ignore')

        # Form the SQL statement
        sql = "INSERT INTO twitter_entity " \
              "(user_name, screen_name, description, " \
              "followers_count, friends_count, " \
              "date_created, tweet_count, language, last_post, " \
              "twitter_id)" \
              " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        # Execute the sql statement
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
        tools.save_object(save_obj, 'cursor_save.pkl')


    @retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_delay=3600000)
    def get_users(self, line):
        return self.api.lookup_users(user_ids=[line])

    def main_loop(self):
        f = open('ids.txt')
        lines = f.readline()
        cursor = self.db.cursor()
        count = 0
        while(lines):
            print i
            if count < 1704200:
                count = count + 100
                continue
            users = self.get_users(lines)
            for user in users:
                self.store_follower(user, cursor)
            lines = f.readline()
            count = count + 100
            print "Finished: ", count, ", waiting 5 seconds..."
            time.sleep(5)

        f.close()
        self.db.close()


a = TwitterEntityFinder()
print "hello"
a.main_loop()

