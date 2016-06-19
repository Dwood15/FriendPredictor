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
					#180 * 200 = 3600 per 15 minutes
					
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
						if(self.tweets_counted > 60):
							if((time.clock() - ctt0) < 2):
								if(self.loud):
									print "Going too fast, slowing down!"
								time.sleep(2.25 - time.clock() - ctt0)
							self.tweets_counted = 0
							ctt0 = time.clock()
						time.sleep(.025)
					
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
				ext_scr = " LIMIT 1000"
			else:
				ext_scr = " ORDER BY tweet_count ASC;"
				
			
			self.selcur.execute(selection_query + ext_scr)
			print "\tExecuted selection query."
			
			time.sleep(15)
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
					self.save_to_csv(result)
					
				if(self.loud):
					print "\tIt took: " + str(time.clock() - t0) + " to get a single user's tweets."
				if((time.clock() - self.last_update) < 8):
					print "too fast for new user, slowing down- waiting for: ", (10 - int(time.clock()-self.last_update))
					time.sleep(10.0 - (time.clock() - self.last_update))
					self.last_update = time.clock()
					
				time.sleep(2.5)
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
		
	def new_csv_for_writing(self, version):
		self.csvfile = 'trackingfile' + str(version) + '.csv'
		with open(self.csvfile, "w") as tracking:
			tracking.write("twitter_id, smallest_pulled_tweet_id, highest_pulled_tweet_id\n")
	
	def save_to_csv(self, tweetresult):
		with open(self.csvfile, "a") as tracking:
			tracking.write("%s, %s, %s\n" % (tweetresult[0], tweetresult[1], tweetresult[2]))
	
		
def entity_min_max_update_from_file(file_name):
	#create a new connection  
	try:
		upDTime = time.clock()
		tdb = tools.db_connect()
		emmcurs = tdb.cursor()
		with open(file_name, 'r') as csvfile:
			reader = csv.reader(csvfile)
			rcount = 0
			for row in reader:
				update_script = "UPDATE twitter_entity SET smallest_pulled_tweet_id = %s, " \
					"highest_pulled_tweet_id = %s WHERE twitter_id = %s"
				emmcurs.execute(update_script, (row[1], row[2], row[0]))
				rcount += 1
				tdb.commit()
				if((rcount % 10) == 0):
					print "Updated 10 rows."
			emmcurs.close()
		
		print "Finished updating from file, it took: " + str(time.clock() - upDTime) + " seconds."
	except Error as e:
		print "user update for user: ", (user_id, min_tweet, max_tweet), " failed."
		print "Message: ", e
		tdb.rollback()


			
def build_script(bot, upper):
#'gaiqtren' = 'get_any_id_query_tweet_count_range_english'
	first_part = "SELECT  twitter_id, smallest_pulled_tweet_id, " \
				"highest_pulled_tweet_id FROM twitter_entity " \
				"WHERE tweet_count >= " + str(bot) 
	second_part = " AND tweet_count < " + str(upper) + " AND twitter_id IS NOT NULL AND language = 'en'"
	return first_part + second_part

#just some stuff so I can do groups of tweeters in series...

def range_status_update(top, range_status):
	if(range_status > 250):
		range_status -= 50
	elif(range_status > 200):
		range_status -= 25
	elif(range_status > 150):
		range_status -= 20
	elif(range_status > 100):
		range_status -= 10
	else:
		range_status = 5
	return range_status
		
range_status = 330
top = 4000
base = top - range_status

tsf = TwitterStatusFinder('trackingfile.csv')

version = 0 

while((base - range_status) > 50):
	#parse the file!
	print "Creating a new user parsing table!"
	thread.start_new_thread(entity_min_max_update_from_file, (str(tsf.csvfile),))
	version += 1
	tsf.new_csv_for_writing(version)
	
	#sleep for about 15secs, try to let some resources free up for a bit...
	time.sleep(15)
	
	#actually execute the main loop
	print "Beginning main loop with base: ", base, " to range: ", top
	mt0 = time.clock() #track the time for the main loop
	tsf.main_loop(build_script(base, top))
	
	print "Took: ", time.clock() - mt0, " seconds to get all the tweets for base: ", base, " to: ", top
	
	top = base
	base = top - range_status
	range_status = range_status_update(top, range_status)

	
tsf.close()
tracking.close()
print "Finished Loop for tweets! base = "