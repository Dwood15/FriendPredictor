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
		" VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9}) ".format(self.id,
		 self.vaderPos, self.vaderNeu, self.vaderNeg,
		 'NULL', 'NULL', 'NULL',
		 'NULL', 'NULL', 'NULL')
		

		query = part_one
		if(loud):
			print "Sentiment query: \n\t: " + query
		
		return query
		
class TwitterSentimentAnalyzer:
	def __init__(self, loud=False):
		self.loud = loud
		t0 = time.clock()

		self.db = tools.db_connect()
		#Fire up three cursors - these should allow for threading.
		self.selcur = self.db.cursor()  #for selecting users
		self.inscur = self.db.cursor()  #inserting the analysis
		
		
		self.last_update = time.clock()
		print str(time.clock() - t0) + " to connect for __init__."
	
	def iter_cursor(self, selCur, num=100):
		while True:
			objects = selCur.fetchmany(num)
			if not objects:
				break
			for object in objects:
				yield object
				
	def main_loop(self, test=False):
		try:
			selection_query = "SELECT tweet_id, tweet_text from tweets"
		#pull all tweets from the database.
			if(test):
				print "Testing! Executing selection query."
				selection_query += " LIMIT 500"
			
			self.selcur.execute(selection_query)
			print "\tExecuted selection query."
			
			startTime = time.clock()
			last_user = None
			
			self.current_tweet_count = 0
			tweet_list = []
			
			for tweet in self.iter_cursor(self.selcur, 5000):
				self.last_update = time.clock()
				
				t0 = time.clock()
				tweet_list.append(TweetSentiment(tweet[0], tweet[1]))
				
				self.current_tweet_count += 1
				if(self.current_tweet_count % 50000 == 0):
					update_tweets(deepcopy(tweet_list), self.loud)
					#thread.start_new_thread(update_tweets, (deepcopy(tweet_list), self.loud))
					time.sleep(3)
					tweet_list = []
				#time.sleep(.0005)
			print "\n\tIt took: "+ str((time.clock() - startTime) / 60) + " minutes to get all tweets."

		except Error as e:
			print "Error receiving from database!!!"
			print e
			sys.exit(1)
			
		finally:
			pass 
	
	def close(self):
		self.selcur.close()
		self.inscur.close()
		
'''Store the analyzed tweet information in the database'''
def analyze_tweet(tweet, sid, loud=False):
	vader = sid.polarity_scores(tweet.text)
	
	tweet.vaderNeg = vader['neg']
	tweet.vaderNeu = vader['neu']
	tweet.vaderPos = vader['pos']
	
	if(loud):
		print "Tweet_text:\n\t" + tweet.text
		for k in sorted(vader):
			print("{0}: {1}, ".format(k, ss[k]))
			
def update_tweets(tweets,loud=False):
	#create a new connection  
	firstTweet = tweets[0].id
	currentTweet = firstTweet
	try:
		upDTime = time.clock()
		tdb = tools.db_connect()
		emmcurs = tdb.cursor()
		for tweet in tweets:
			analyze_tweet(tweet, SentimentIntensityAnalyzer())
			update_script = tweet.get_query(loud)
			emmcurs.execute(update_script)
			currentTweet = tweet.id
		
		tdb.commit()

		emmcurs.close()
		print "Updated tweet analysis stuff" 
		
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
