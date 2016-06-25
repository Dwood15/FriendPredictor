import json
import tweepy
from riotwatcher import RiotWatcher

def get_json_secret():
    secret_file = "secret.json"
    secret = open(secret_file, "r")
    file_string = secret.read()
    return json.loads(file_string)

def unicode_to_utf8(input):
    if isinstance(input, dict):
        return {unicode_to_utf8(key): unicode_to_utf8(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [unicode_to_utf8(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def lol_connect():
    file_json = get_json_secret()
    return RiotWatcher(file_json['riot_key'])

def api_connect():
    file_json = get_json_secret()
    auth = tweepy.OAuthHandler(file_json['key'], file_json['secret'])  # AppAuth or OAuth?
    auth.set_access_token(file_json['token'], file_json['token_secret'])
    return tweepy.API(auth)


def db_connect():
    file_json = get_json_secret()
    # because mysqldb isn't playing nice.
    if (file_json['uname'] == 'dason'):
        print "using MySQL, NOT MySQLdb"
        import mysql.connector as connection
        from mysql.connector import MySQLConnection, Error
        cnct = "msql"
    else:
        print "using MySQLdb"
        import MySQLdb as connection
        cnct = "msqldb"

    db = connection.connect(host=file_json['host'], port=3306, user=file_json['uname'], passwd=file_json['upwd'],
                            db="lol")

    # Intended to be temporary until I hear if mysqldb plays nice with mysql connect.
    if (cnct == "msql"):
        return db
    else:
        return db
