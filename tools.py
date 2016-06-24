import json
import tweepy

#TODO: Add LOL_connect functions

def api_connect():
	secret_file = "secret.json"
	secret = open(secret_file, "r")
	file_string = secret.read()
	file_json = json.loads(file_string)
	auth = tweepy.OAuthHandler(file_json['key'], file_json['secret'])  # AppAuth or OAuth?
	auth.set_access_token(file_json['token'], file_json['token_secret'])
	return tweepy.API(auth)

def db_connect():
	secret_file = "secret.json"
	secret = open(secret_file, "r")
	file_string = secret.read()
	file_json = json.loads(file_string)
	
	#because mysqldb isn't playing nice.
	if(file_json['piname'] =='dason'):
		print "using MySQL, NOT MySQLdb"
		import mysql.connector as connection
		cnct = "msql"
	else:
		print "using MySQLdb"
		import MySQLdb as connection
		cnct = "msqldb"
		
	db = connection.connect(host=file_json['localserver'],user=file_json['localuser'], db="lol", use_unicode=True,charset='utf8mb4',collation='utf8mb4_general_ci')
	
	#Intended to be temporary until I hear if mysqldb plays nice with mysql connect.
	if(cnct == "msql"):
		return db
	else:
		return db