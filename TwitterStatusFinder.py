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
		tup = tools.db_connect()
		#see the tuples in tools.py.
		self.dbcur = tup.cursor()
		
		print "Executing query!"
		
		try:
		#pull the selected accounts from the database.
			if(test):
				print "Testing!"
				self.dbcur.execute(selection_query + " LIMIT 1")
				print "Fetching one!"
				self.currentUser = self.dbcur.fetchone()
				
				if(self.currentUser is not None):
					print "Success! got a row: " + str(self.currentUser)
				self.get_tweets()
				self.dbcur.close()
			else:
				self.dbcur.execute(selection_query + "ORDER BY tweet_count, DESC")
				print 'Getting Many users'
				self.currentUser = dbcur.fetchmany(100)
				
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
		
	def get_tweets(self):
			currentTweet = None
			if(self.currentUser[1] is not None and self.currentUser[2] is not None):
				print "We've stored this user's tweets before!"
			
				print "storing for new user!"
				
				print "WHOA, half-baked ids up in here! careful bessy."
				print "Don't worry, we'll just overwrite them I guess."
			
			if(currentTweet is not None):
				print "Received tweet! Here's the text: "
				print currentTweet.text
			else:
				print "Didn't get anything from the tweet query."
	def process_statuses(self):
		pass
	def get_next_user(self):
		print 'Getting next user!'
		self.currentUser = next(self.currentUser)
		
		
#'gaiqtren' = 'get_any_id_query_tweet_count_range_english'
gaiqtcr = "SELECT twitter_id, smallest_pulled_tweet_id, highest_pulled_tweet_id FROM twitter_entity WHERE tweet_count > 0 AND tweet_count < 50 "
tsf = TwitterStatusFinder(gaiqtcr, True)
