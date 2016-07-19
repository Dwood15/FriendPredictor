import pickle
import datetime
import tools
import tweepy
import pprint
import time
import sys
import inspect
import thread
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from mysql.connector import MySQLConnection, Error
from copy import deepcopy

#threaded decorator
def threaded(fn):
	def wrapper(*args, **kwargs):
		threading.Thread(target=fn, args=args, kwargs=kwargs).start()
	return wrapper


class TweetSentiment:
	def __init__(self, tweet_id, text, vaderPos=None, vaderNeu=None, vaderNeg=None, 
				pos2=None, neu2=None, neg2=None, pos3=None, neu3=None, neg3=None):
		self.id = tweet_id
		self.vaderPos = vaderPos
		self.vaderNeu = vaderNeu
		self.vaderNeg = vaderNeg
		
		self.pos2 = pos2
		self.neu2 = neu2
		self.neg2 = neg2
		
		self.pos3 = pos3
		self.neu3 = neu3
		self.neg3 = neg3

		self.text = text
		
	'''Warning, no protection against SQL Injection attacks!'''
	def get_query(self, loud=False):
		
		part_one = "INSERT INTO twitter_sentiment " \
		"(tweet_id, posVader, neuVader, negVader, pos2, neu2, neg2, pos3, neu3, neg3 )" \
		" VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}) ON DUPLICATE KEY UPDATE tweet_id = tweet_id ".format(self.id,
		 self.vaderPos, self.vaderNeu, self.vaderNeg,
		 'NULL', 'NULL', 'NULL',
		 'NULL', 'NULL', 'NULL')

		query = part_one
		if(loud):
			print "Sentiment query: \n\t: " + query
		
		return query
		
	'''Store the analyzed tweet information in the database'''
	def analyze_self(self, sid, loud=False):
		vader = sid.polarity_scores(self.text)
	
		self.vaderNeg = vader['neg']
		self.vaderNeu = vader['neu']
		self.vaderPos = vader['pos']
	
		if(loud):
			print "Tweet_text:\n\t" + self.text
			for k in sorted(vader):
				print("{0}: {1}, ".format(k, ss[k]))
			
class TwitterSentimentAnalyzer:
	def __init__(self, loud=False):
		self.loud = loud
		t0 = time.clock()

		self.db = tools.db_connect()
		#Fire up three cursors - these should allow for threading.
		self.selcur = self.db.cursor()  #for selecting users
		
		self.last_update = time.clock()
		print str(time.clock() - t0) + " to connect for __init__."
	
	def iter_cursor(self, selCur, num=100):
		while True:
			objects = selCur.fetchmany(num)
			if not objects:
				break
			for object in objects:
				yield object
				
	def main_loop(self):
		try:
			selection_query = "SELECT tw.tweet_id, tw.tweet_text from tweets tw LEFT JOIN twitter_sentiment ts ON tw.tweet_id = ts.tweet_id WHERE ts.tweet_id IS NULL;"
			#pull all tweets from the database.

			print "Executing selection query"
			self.selcur.execute(selection_query)
			print "\tExecuted selection query."
			
			startTime = time.clock()
			last_user = None
			
			self.current_tweet_count = 0
			
			start_region = 0
			tweet_list = []
			sid = SentimentIntensityAnalyzer()
			if(self.loud):
				print "Beginning tweet analysis, etc."
				
			for tweet in self.iter_cursor(self.selcur, 3000):
				self.last_update = time.clock()
				
				t0 = time.clock()
				tweet_list.append(TweetSentiment(tweet[0], tweet[1]))
				tweet_list[self.current_tweet_count].analyze_self(sid)
				
				if(self.current_tweet_count > 0):
					if(self.current_tweet_count % 250001 == 0):
						thread.start_new_thread(update_tweets, (tweet_list[start_region:self.current_tweet_count],))
						start_region = self.current_tweet_count
						if(self.loud):
							print "Fired off new thread!"
					elif(self.current_tweet_count % 2500 == 0 and self.loud):
						print "Analyzed 2500 tweets! tweet count at: " + str(self.current_tweet_count)
					elif(self.current_tweet_count < 2500 and self.current_tweet_count % 50 == 0 and self.loud):
						print "Current Tweet count: " + str(self.current_tweet_count)
						
				self.current_tweet_count += 1
				
			print "\n\tIt took: "+ str((time.clock() - startTime) / 60) + " minutes to get " + str(self.current_tweet_count) + " tweets."
			
			update_tweets(tweet_list[start_region:self.current_tweet_count], self.loud)
			
		except Error as e:
			print "Error receiving from database!!!"
			print e
			sys.exit(1)
			
		finally:
			pass 
	
	def close(self):
		self.selcur.close()
	
def update_tweets(tweets,loud=False):
	if tweets is not None:

		#create a new connection  
		firstTweet = tweets[0].id
		currentTweet = firstTweet
		try:
			upDTime = time.clock()
			tdb = tools.db_connect()
			emmcurs = tdb.cursor()
			count = 0
			for tweet in tweets:
				update_script = tweet.get_query(loud)
				emmcurs.execute(update_script)
				currentTweet = tweet.id
				count += 1
				if(count % 250):
					tdb.commit()
					count = 0
			tdb.commit()
			emmcurs.close()
			
		except Error as e:
			print "Updating tweets: ", (currentTweet), " failed."
			print "Message: ", e
			tdb.rollback()
		
		
tsa = TwitterSentimentAnalyzer()

#execute the main loop
print "Beginning main loop!"
mt0 = time.clock() #track the time for the loop
tsa.main_loop()

print "Took: ", ((time.clock() - mt0) / 60), " minutes to get all the tweets!"

tsa.close()
print "Finished loop for tweets!"
