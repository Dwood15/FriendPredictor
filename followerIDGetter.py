import tools
import tweepy
import time
from retrying import retry

class FollowerIdGetter:
    def __init__(self, screen_name):
        self.api = tools.api_connect()
        self.pages = tweepy.Cursor(self.api.followers_ids, screen_name=screen_name).pages()

    @retry(wait_exponential_multiplier=1000, wait_exponential_max=10000, stop_max_delay=9600000)
    def limit_handled(self, cursor):
        while True:
            try:
                yield cursor.next()
            except tweepy.RateLimitError:
                print "RATE LIMIT EXCEPTION... WAITING 15 min"
                time.sleep(15 * 60)

    def main_loop(self):
        id_file = open("ids.txt", "w")
        follower_ids = ''
        count = 0
        for page in self.limit_handled(self.pages):
            print " len: ", len(page)
            for i, id in enumerate(page, 1):
                if i % 100 is not 0:
                    follower_ids += str(id) + ', '
                else:
                    follower_ids += str(id) + '\n'
                if i % 100 == 0 and i is not 0:
                    id_file.write(follower_ids)
                    count += 100
                    print "Have now stored: ", count, " ids."
                    follower_ids = ''
            time.sleep(60)

        self.db.close()
        id_file.close()


fig = FollowerIdGetter('LeagueofLegends')

fig.main_loop()