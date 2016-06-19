import pickle
import datetime
import tools
import tweepy
import pprint
import time
import sys
import inspect

from retrying import retry
from mysql.connector import MySQLConnection, Error

from retrying import retry

class TwitterStatusFinder:
	def __init__(self, loud=False):
		self.t0 = time.clock()
		self.api = tools.api_connect()
		#self.api.wait_on_rate_limit = True
		
		self.loud = loud
		
		print str(self.update_clock()) + " for connecting to Twitter."
		
		self.db = tools.db_connect()
		#see the tuples in tools.py.
		self.selcur = self.db.cursor()
		self.inscur = self.db.cursor()
		
		print str(self.update_clock()) + " to connect for __init__."
	
	def update_clock(self):
		tsince = time.clock() - self.t0
		self.t0 = time.clock()
		return tsince
	
	def iter_users(self, selCur, num=100):
		while True:
			users = selCur.fetchmany(num)
			if not users:
				break
			for user in users:
				yield user
	
	def get_tweets(self, user_Id=None, count=200, test=False):
		try:
			if(user_Id is not None):
				userId = user_Id[0]
				min_id = user_Id[1]
				max_id = user_Id[2]
				currentTweet = None

				if(min_id is not None and max_id is not None):
					if(self.loud):
						print "We've stored this user's tweets before!"
					currentTweet = tweepy.Cursor(self.api.user_timeline, trim_user=True, user_id=userId, count=count, contributor_details=False, since_id=max_id).items()
					
				elif(min_id is None and max_id is None):
					if(self.loud):
						print "Storing for new user!"
					currentTweet = tweepy.Cursor(self.api.user_timeline, trim_user=True, user_id=userId, count=count, contributor_details=False).items()
					
				else:
					print "WHOA, half-baked ids up in here! Slow down bessy."
					print "user_id: " + str(userId) + " min_id: " + str(min_id) + " max_id: " + str(max_id)
					print "Exiting..."
					sys.exit(1)
				
				if(currentTweet is not None):
					print "Received tweets!"
					upUser = False
					for tweet in currentTweet:
						if(self.loud):
							print tweet.text.encode('UTF-8', 'ignore')
						if(self.store_tweet(tweet, userId, test)):
							#only worry about max/min id if the storage worked!
							if(tweet.id > max_id or max_id is None):
								max_id = tweet.id
								upUser = True
							elif (tweet.id < min_id or min_id is None):
								min_id = tweet.id
								upUser = True
								
					if(upUser and test == False):
						update_user = "UPDATE twitter_entity SET smallest_pulled_tweet_id = %s, highest_pulled_tweet_id = %s WHERE twitter_id = %s"
						try:
							self.inscur.execute(update_user, (min_id, max_id, userId))
							self.db.commit()
						except Error as e:
							print e
							self.db.rollback()
					#time.sleep(1)
				
				else:
					print "Didn't get anything from tweets query!"
			else:
				print "User_id is none, please specify a valid user_id"
				sys.exit(1)
				
		except tweepy.TweepError as te:
			print "\n\t ERROR code: ", te.response.status_code
			stat_code = te.response.status_code
			if(stat_code == 401):
				print "\n\t\tUnable to pull a user's tweets! User_Id: " + str(user_Id[0])
			elif(te.api_code == 88 or stat_code == 429 ):
				print "\n\tSlow down! Too many requests! sleeping for 15 minutes!"
				time.sleep(60 * 5)
				
			else:
				print "\n\tUnknown error, code: ", te.response.status
				print te.message
				sys.exit(1)
			
	def store_tweet(self, tweet, userId, test=False):
		tweet_id = tweet.id
		text = tweet.text.encode('UTF-8', 'ignore')
		date = str(tweet.created_at).encode('UTF-8', 'ignore')
		user_id =  int(userId)
		rt_count = tweet.retweet_count
		reply_to_tweet = tweet.in_reply_to_status_id
		reply_to_user = tweet.in_reply_to_user_id
		
		insert_script = "INSERT IGNORE INTO tweets " \
						"(tweet_id, tweet_text, created_at," \
						" twitter_id, retweet_count," \
						" in_reply_to_status_id, in_reply_to_twitter_id )" \
						" VALUES (%s, %s, %s, %s, %s, %s, %s)"
						
		args = (tweet_id, text, date, user_id, rt_count, reply_to_tweet, reply_to_user)
		
		if(test or self.loud):
			print "\nAll args: " + str(args)
			print "Storing tweet by id: " + str(tweet_id)
			print "Encoded text: " + text
			print "Encoded Date: " + date
			print "Encoded user_id: " + str(user_id)
			print "Retweet count: " + str(rt_count)
			print "Reply to tweet " + str(reply_to_tweet)
			print "Reply to user " + str(reply_to_user)
			
		if(not test):
			try: 
				self.inscur.execute(insert_script, args)	
				self.db.commit()
			except Error as e:
				print e
				self.db.rollback()
				return False
			
		return True
		
	def main_loop(self, selection_query, test=False):
		try:
		#pull the selected accounts from the database.
		#I suppose this should be moved to some kind of main loop.
			if(test):
				print "Testing! Executing selection query."
				ext_scr = " LIMIT 10000"
			else:
				ext_scr = " ORDER BY tweet_count DESC;"
				
			
			self.selcur.execute(selection_query + ext_scr)
			startTime = time.clock()
			last_user = None
			for user in self.iter_users(self.selcur, 100):
				if(last_user is not None):
					if(user[0] == last_user):
						print "\t******Repeating users, something wrong with iter_users******"
						sys.exit(1)
				else:
					last_user = user[0]
					
				print "\n\n"	
				self.t0 = time.clock()
				self.get_tweets(user, count=200, test=test)
				print "\t\tIt took: " + str(time.clock() - self.t0) + " to get a single user's tweets."
				time.sleep(2)
			print "\n\tIt took: "+ str(time.clock() - startTime) + " to get all user's tweets."
			self.selcur.close()
			self.inscur.close()
		except Error as e:
			print "Error receiving from database!!!"
			print e
			sys.exit(1)
			
		finally:
			pass 
			
def build_script(bot, upper):
#'gaiqtren' = 'get_any_id_query_tweet_count_range_english'
	first_part = "SELECT twitter_id, smallest_pulled_tweet_id, " \
				"highest_pulled_tweet_id FROM twitter_entity " \
				"WHERE tweet_count > " + str(bot)
	second_part = " AND tweet_count < " + str(upper)
	return first_part + second_part

base = 0
range_status = 7
tsf = TwitterStatusFinder()

top = base + range_status

while(base < 1500):
	mt0 = time.clock()
	top = base + range_status
	tsf.main_loop(build_script(base, top))
	base = base + range_status
	range_status += int(range_status / 3)
	print "Took: ", time.clock() - mt0, " seconds to get all the tweets for base: ", base, " to: ", top
	time.sleep(60 * 4)

print "Finished Loop for tweets! base = "