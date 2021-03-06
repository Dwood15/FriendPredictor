import pickle
import datetime
import tools
import tweepy
import pprint
import time
from retrying import retry

print "Testing basic functions."

#TODO: Add league of Legends checks.
#\033[91m is an ASCII color escape sequence for Windows terminal/cmd.

api = tools.api_connect()
db = tools.db_connect()


#get a cursor for executing stuffs
dcur = db.cursor()
#predefine it so it carries over.
row = None

#try executing a SQL query on the remote database.
try:
	sql = "SELECT twitter_id FROM twitter_entity WHERE tweet_count = 1 LIMIT 1"
	dcur.execute(sql);
	row = dcur.fetchone()
	if(row is not None):
		print(row)

		print "It seems something was returned, id: " + str(row[0])
	else:
		print "Query: " + sql
		print "Was unable to return anything!"
	
except MySQL.Error, e:
	print "Error receiving from database!!!"
	print e.args[0], e.args[1]
	
finally:
	dcur.close()
	db.close()

tweet = None

#try getting some stuff from the Twitter API here:
if(row is not None):
	try:
		tweet = next(tweepy.Cursor(api.user_timeline, user_id=row[0], count=1, trim_user=True, contributor_details=False).items(1))
		
		if(tweet is not None):
			print "Received tweet! here's the text: "
			print tweet.text
		else:
			print "\03Didn't get anything from the tweet query."
			
	except tweepy.TweepError, e:
		print "Had an error with tweet. Not sure what to do."
		for property, value in vars(e.response).iteritems():
			print property, ": ", value
		pass
		print e.response.headers['x-rate-limit-remaining']
	
	finally:	
		pass
		
else:
	print "\033[91mUnable to get anything from test query, NOT trying Twitter."