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
    if (file_json['piuser'] == 'dason'):
        print "using MySQL, NOT MySQLdb"
        import mysql.connector as connection
        cnct = "msql"
    else:
        print "using MySQLdb"
        import MySQLdb as connection
        cnct = "msqldb"

    db = connection.connect(host=file_json['piserver'], user=file_json['piuser'], passwd=file_json['pipwd'], db="lol", use_unicode=True,
                            charset='utf8mb4', collation='utf8mb4_general_ci')
    if (cnct == "msql"):
        return db
    else:
        return db


