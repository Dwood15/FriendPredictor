import tweepy
import json
import pprint
import time

def api_connect():
    secret_file = "secret.json"

    secret = open(secret_file, "r")

    file_string = secret.read()

    file_json = json.loads(file_string)

    auth = tweepy.OAuthHandler(file_json['key'], file_json['secret'])

    auth.set_access_token(file_json['token'], file_json['token_secret'])

    return tweepy.API(auth)


api = api_connect()

lol = api.get_user("LeagueOfLegends")


possible_players = []

followers = tweepy.Cursor(api.followers, screen_name="LeagueOfLegends").items()

while True:
    try:
        follower = next(followers)
        print follower.description
    except tweepy.TweepError as error:
        print "waiting for 15 min: ", error
        time.sleep(60*15)
    except StopIteration:
        break
    if "IGN: " in follower.description or "in game name" in follower.description :
        print follower
        possible_players.append(follower)




for i in possible_players:
    print i