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
	if(file_json['uname'] =='dason'):
		print "using MySQL, NOT MySQLdb"
		import mysql.connector as connection
		cnct = "msql"
	else:
		print "using MySQLdb"
		import MySQLdb as connection
		cnct = "msqldb"
		
	db = connection.connect(host="159.118.221.28",port=3306,user=file_json['uname'],passwd=file_json['upwd'], db="lol")
	
	#Intended to be temporary until I hear if mysqldb plays nice with mysql connect.
	if(cnct == "msql"):
		return (db, cnct)
	else:
		return db