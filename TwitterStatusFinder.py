import pickle
import datetime
import tools
import tweepy
import pprint
import time
import sys
from mysql.connector import MySQLConnection, Error

from retrying import retry

class TwitterStatusFinder:
	def __init__(self, selection_query, test = False):
		self.api = tools.api_connect()
		tmp = tools.db_connect()
		#see the tuples in tools.py.
		self.selcur = tmp.cursor()
		self.inscur = tmp.cursor()

		try:
		#pull the selected accounts from the database.
			if(test):
				print "Testing!"
				self.selcur.execute(selection_query + " LIMIT 1")
				print "Fetching one!"
				self.currentUser = self.selcur.fetchone()
				
				if(self.currentUser is not None):
					print "Success! got a row: " + str(self.currentUser)
				
				self.get_tweets(self.currentUser, count=200)
				self.store_tweet()
				self.selcur.close()
			else:
				self.selcur.execute(selection_query + "ORDER BY tweet_count, DESC")
				print 'Getting Many users'

				
			if self.currentUser is not None:
				print "Success! Connected to database, and recvd data!"
			else:
				print "\033[91mQuery: \n\t" + selection_query
				print "\033[91mTurned up empty! Adjust the query."
				sys.exit(1)
			
		except Error as e:
			print "\033[91mError receiving from database!!!"
			print e
			sys.exit(1)
			
		
		#don't want to close the cursor when we don't have to...
		finally:
			pass 
	
	def store_tweet(self, tweet, cursor, userData, minMax, test=False):
		print "Storing tweet by id: " + str(tweet_id)
		tweet_id = tweet.id
		text = tweet.text.encode('ascii', 'ignore')
		print "Encoded text: " + text
		date = str(tweet.created_at).encode('ascii', ignore)
		print "Encoded Date: " + date
		user_id =  int(tweet.id)
		print "Encoded user_id: " + str(user_id)
		rt_count = tweet.retweet_count
		print "Retweet count: " + str(rt_count)
		reply_to_tweet = int(tweet.in_reply_to_status_id)
		print "Reply to tweet " + str(reply_to_tweet)
		
		reply_to_user = int(tweet.in_reply_to_twitter_id)
		print "Reply to user " + str(reply_to_user)
		
		
		insert_script = "INSERT INTO tweets " \
						"(tweet_id, tweet_text, created_at," \
						" twitter_id, retweet_count," \
						" in_reply_to_status_id, in_reply_to_twitter_id," \
						" possibly_sensitive)" \
						" VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
		args = (tweet_id, text, date, user_id, rt_count, reply_to_tweet, reply_to_user, int(twitter_id))
		print "\nAll args: " + args
		#try: 
			#cursor.execute(insert_script, args)
	#get users in groups of 100 by default.
	def iter_users(self, num=100):
		while True:
			users = self.selcur.fetchmany(num)
			if not users:
				break
			for user in users:
				yield user
			
	def get_tweets(self, user_Id=None, count=200, dbcur):
		if(user_Id is not None):
			userId = user_Id[0]
			min_id = user_Id[1]
			max_id = user_Id[2]
			currentTweet = None
			tweets = []
			if(min_id is not None and max_id is not None):
				currentTweet = next(tweepy.Cursor(self.api.user_timeline, trim_user=True, user_id=userId, count=count, contributor_details=False, since_id=max_id))
				print "We've stored this user's tweets before!"
			
			elif(min_id is None and max_id is None):
				print "Storing for new user!"
				currentTweet = tweepy.Cursor(self.api.user_timeline, trim_user=True, user_id=userId, count=count, contributor_details=False).items()
				
			else:
				print "WHOA, half-baked ids up in here! Slow down bessy."
				print "user_id: " + str(userId) + " min_id: " + str(min_id) + " max_id: " + str(max_id)
				print "Exiting..."
				sys.exit(1)
			
			if(currentTweet is not None):
				print "Received tweets! Here's the text: "
				upUser = False
				for tweet in currentTweet:
					print tweet.text
					if(tweet.id > max_id or max_id is None):
						max_id = tweet.id
					elif (tweet.id < min_id is None):
						min_id = tweet.id
						
			else:
				print "Didn't get anything from tweets query!"
		else:
			print "User_id is none, please specify a valid user_id"
			sys.exit(1)
			
		for tweet in tweets:
			store_tweet(tweet, self.dbcur, )
		#essentially: 
		#for account in accounts:
		#	tweets_add = []
		#	for tweet in tweets:
		#		tweets_add.add(tweet)
			#build list of tweets in sql-handy format
			#insert into database
			
#'gaiqtren' = 'get_any_id_query_tweet_count_range_english'
select_script = "SELECT twitter_id, smallest_pulled_tweet_id, highest_pulled_tweet_id FROM twitter_entity WHERE tweet_count > 0 AND tweet_count < 10 "
tsf = TwitterStatusFinder(select_script, True)
