import pickle
import datetime
import tools
import tweepy
import pprint
import time
import sys
import inspect
import csv
import thread

from mysql.connector import MySQLConnection, Error
#import MySQLdb


class TwitterStatusFinder:
	def __init__(self, file, loud=False):
		
		self.csvfile = file
		self.loud = loud
		self.t0 = time.clock()
		
		self.est_connections()
		self.db = tools.db_connect()
		#cursors
		self.selcur = self.db.cursor()
		self.inscur = self.db.cursor()
		self.tweets_counted = 0
		self.last_update = time.clock()
		self.cumulative = 0
		print str(self.update_clock()) + " to connect for __init__."
	
	def update_clock(self):
		tsince = time.clock() - self.t0
		self.t0 = time.clock()
		return tsince
		
	def est_connections(self):
		self.api = tools.api_connect()
		self.api.wait_on_rate_limit = True
		self.api.wait_on_rate_limit_notify = True
		
	def iter_users(self, selCur, num=100):
		while True:
			users = selCur.fetchmany(num)
			if not users:
				break
			for user in users:
				yield user
	
	def get_tweets(self, user_Id=None, count=200, test=False, retrying=0):
		if(retrying > 0):
			if(self.loud):
				print "Reestablishing connections, try #: ", retrying
			self.est_connections()

		try:
			if(user_Id is not None):
				userId = user_Id[0]
				min_id = user_Id[1]
				max_id = user_Id[2]
				currentTweet = None
				tweets_since_message = 0
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
					#print "Received tweets!"
					upUser = False
					#need a tweetsPerMinute calculator...
					#180 requests of up to 200 tweets per 15 minutes
					#180 * 200 = 36000 per 15 minutes
					
					ctt0 = time.clock()
					for tweet in currentTweet:
						if(self.store_tweet(tweet, userId, test)):
							#only worry about max/min id if the storage worked!
							if(tweet.id > max_id or max_id is None):
								max_id = tweet.id
								upUser = True
							elif (tweet.id < min_id or min_id is None):
								min_id = tweet.id
								upUser = True
						self.tweets_counted += 1 #count tweets even if they failed...
						tweets_since_message += 1
						if(tweets_since_message > 180):
							print "Still working on user: ", userId
							tweets_since_message = 0
							
						if(self.tweets_counted > 60):
							if((time.clock() - ctt0) < 2):
								if(self.loud):
									print "Going too fast, slowing down!"
								time.sleep(2.15 - (time.clock() - ctt0))
							self.tweets_counted = 0
							ctt0 = time.clock()
						time.sleep(.015)
					self.cumulative = 0
					if(upUser and test == False):
						return (userId, min_id, max_id)
					else:
						return None
				else:
					print "Didn't get anything from tweets query!"

			else:
				print "User_id is none, please specify a valid user_id - attempting to skip."
				print user_Id
				
		except tweepy.TweepError as te:
			print te.message
			print "API code: ", te.api_code
			if(hasattr(te.response, 'status_code') and te.response.status_code is not None):
				print "\t ERROR code: ", te.response.status_code
				stat_code = te.response.status_code
				if(stat_code == 401):
					print "\tUnable to pull a user's tweets! User_Id: " + str(user_Id[0])
					remain = te.response.headers['x-rate-limit-remaining']
					print "\t", remain, " remaining"
					if (remain < 60):
						time.sleep(15)
				elif(te.api_code == 88 or stat_code == 429 ):
					print "\tSlow down! Too many requests! sleeping for %s seconds!" % (self.cumulative)
					self.cumulative += 15
					time.sleep(self.cumulative)
			else:
				print "\n\tUnknown error... "
				if(retrying < 4):
					time.sleep(5 + (15 * retrying))
					self.est_connections()
					return self.get_tweets(user_Id, count, retrying=(retrying + 1))
				else:
					print "retrying the connection failed miserably."
					sys.exit(1)
					
		except Error as e:
			print "\n\tget_tweets error: ", e

		return None
		
	def store_tweet(self, tweet, userId, test=False):
		tweet_id = tweet.id
		text = tweet.text.encode('UTF-8', 'ignore')
		date = str(tweet.created_at).encode('UTF-8', 'ignore')
		user_id =  int(userId)
		rt_count = tweet.retweet_count
		reply_to_tweet = tweet.in_reply_to_status_id
		reply_to_user = tweet.in_reply_to_user_id
		if(self.loud):
			print "Storing tweets"
		insert_script = "INSERT INTO tweets " \
						"(tweet_id, tweet_text, created_at," \
						" twitter_id, retweet_count," \
						" in_reply_to_status_id, in_reply_to_twitter_id )" \
						" VALUES (%s, %s, %s, %s, %s, %s, %s)" \
						" ON DUPLICATE KEY UPDATE tweet_id = tweet_id"
						
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
				selection_query += " LIMIT 500"

				
			
			self.selcur.execute(selection_query)
			print "\tExecuted selection query."
			
			time.sleep(5)
			startTime = time.clock()
			last_user = None
			
			for user in self.iter_users(self.selcur, 300):
				self.last_update = time.clock()
				print "New user!"
				if(last_user is not None):
					if(user[0] == last_user):
						print "\t******Repeating users, something wrong with iter_users******"
						print "Attempting to skip"
				else:
					last_user = user[0]
					print "Last user is None: ", user
				t0 = time.clock()
				result = self.get_tweets(user, count=200, test=test)
				if(result is not None):
					thread.start_new_thread(entity_min_max_update, (result,))
					
				if(self.loud):
					print "\tIt took: " + str(time.clock() - t0) + " to get a single user's tweets."
				if((time.clock() - self.last_update) < 7.0):
					print "too fast for new user, slowing down- waiting for: ", (8.0 - time.clock()-self.last_update)
					time.sleep(8.0 - (time.clock() - self.last_update))
					self.last_update = time.clock()
					
				time.sleep(2.0)
			print "\n\tIt took: "+ str(time.clock() - startTime) + " to get all user's tweets."

		except Error as e:
			print "Error receiving from database!!!"
			print e
			sys.exit(1)
			
		finally:
			pass 
	
	def close(self):
		self.selcur.close()
		self.inscur.close()
	
def entity_min_max_update(row):
	#create a new connection  
	try:
		upDTime = time.clock()
		tdb = tools.db_connect()
		emmcurs = tdb.cursor()
		update_script = "UPDATE twitter_entity SET smallest_pulled_tweet_id = %s, " \
				"highest_pulled_tweet_id = %s WHERE twitter_id = %s " \
				" AND highest_pulled_tweet_id <= %s AND smallest_pulled_tweet_id >= %s"
		emmcurs.execute(update_script, (row[1], row[2], row[0], row[1], row[2]))
		tdb.commit()

		emmcurs.close()
		print "Updated USER'S minmax! " + str(row[0]) 
		
	except Error as e:
		print "user update for user: ", (row[0], row[1], row[2]), " failed."
		print "Message: ", e
		tdb.rollback()

def build_script():
    # 'gaiqtren' = 'get_any_id_query_tweet_count_range_english'
        first_part = "SELECT te.twitter_id, te.smallest_pulled_tweet_id, te.highest_pulled_tweet_id"
        second_part = " From twitter_lol_resolution tlr JOIN twitter_entity te ON te.entity_id = tlr.twitter_entity_id "\
					  " ORDER BY te.tweet_count DESC"
        return first_part + second_part



# just some stuff so I can do groups of tweeters in series...

tsf = TwitterStatusFinder('trackingfile.csv')

#execute the main loop
print "Beginning main loop!"
mt0 = time.clock() #track the time for the loop
tsf.main_loop(build_script())

print "Took: ", ((time.clock() - mt0) / 60), " minutes to get all the tweets!"

tsf.close()
print "Finished loop for tweets!"
