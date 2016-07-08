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
from nltk.sentiment.vader import SentimentIntensityAnalyzer
#import MySQLdb

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
	def update_self(self, insCur, loud=False):
		buildStr = "INSERT INTO twitter_sentiment " \
		"(posVader, neuVader, negVader, pos2, neu2, neg2, pos3, neu3, neg3 )" \
		"VALUES ({0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}, {8}, {9})"\
		"ON DUPLICATE KEY UPDATE "\
		"posVader = {1}, neuVader = {2}, , negVader = {3}, "\
		"pos2 = {4}  neu2 = {5},  neg2 = {6}, "\ 
		"pos3 = {7},  neu3 = {8},  neg3 = {9}"
		
		query = str.format(buildStr, 
		(self.vaderPos, self.vaderNeu, self.vaderNeg,
		 self.pos2, self.neu2, self.neg2,
		 self.pos3, self.neu3, self.neg3
		))
		if(loud):
			print "Query: \n" + query
		
		self.inscur.execute(insert_script, args)	
		self.db.commit()

	def analyze_tweet(self, analysis_object, loud=False):
		vader = sid.polarity_scores(self.text)
		
		if(loud):
			print "Tweet_text:\n\t" + self.text
			for k in sorted(vader):
				print("{0}: {1}, ".format(k, ss[k]))
class TwitterSentimentAnalyzer:
	def __init__(self, file, loud=False):
		self.loud = loud
		t0 = time.clock()
		
		self.est_connections()
		self.db = tools.db_connect()
		#Fire up three cursors - these should allow for threading.
		self.selcur = self.db.cursor()  #for selecting users
		self.twecur = self.db.cursor()  #getting tweets for user,
		self.inscur = self.db.cursor()  #inserting the analysis
		
		
		self.last_update = time.clock()
		print str(time.clock() - t0) + " to connect for __init__."
	
	def iter_cursor(self, selCur, num=100):
		while True:
			users = selCur.fetchmany(num)
			if not users:
				break
			for user in users:
				yield user

	'''Get a list of tweets from DB, and then fire off thread to analyze and update them.'''
	def get_tweets(self, user_Id=None, count=200, test=False, retrying=0):
		
					
		except Error as e:
			print "\n\tget_tweets error: ", e

		return None
	
	'''Store the analyzed tweet information in the database'''
	def store_analyzer(self, tweet, dataTuple, test=False):
		tweet_id = tweet.id
		
		if(self.loud):
			print "Storing tweets"
		insert_script = "INSERT INTO tweets " \
						"(tweet_id, tweet_text, created_at," \
						" twitter_id, retweet_count," \
						" in_reply_to_status_id, in_reply_to_twitter_id )" \
						" VALUES (%s, %s, %s, %s, %s, %s, %s)" \
						" ON DUPLICATE KEY UPDATE tweet_id = tweet_id"
						
		args = (tweet_id, text, date, , rt_count, reply_to_tweet, reply_to_user)
		
		if(test or self.loud):
			print "\nAll args: " + str(args)
			print "Storing tweet by id: " + str(tweet_id)
			print "Vader pos: " 
			
			
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
				print "Analyzing new user!"
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
