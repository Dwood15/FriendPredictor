import json
import tweepy
import MySQLdb


def api_connect():
    secret_file = "secret.json"
    secret = open(secret_file, "r")
    file_string = secret.read()
    file_json = json.loads(file_string)
    auth = tweepy.OAuthHandler(file_json['key'], file_json['secret'])  # AppAuth or OAuth?
    auth.set_access_token(file_json['token'], file_json['token_secret'])
    return tweepy.API(auth)


def db_connect():
    db = MySQLdb.connect("localhost", "root", "", "lol")
    return db


