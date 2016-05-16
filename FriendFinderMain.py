from riotwatcher import RiotWatcher
from RiotJSONToCSV import *

rw = RiotWatcher()

def getSummonerByName(n):
	return rw.get_summoner(name=n)

def getSummonerLeagueByIDs(summonerIds=[], reg='na'):
	return rw.get_league(summoner_ids=summonerIds, region=reg)

def getSummonerLeagueEntryByIDs(summonerIds=[], reg='na'):
	return rw.get_league_entry(summoner_ids=summonerIds, region=reg)
	
#https://developer.riotgames.com/api/methods#!/985/3356
# check if we have API calls remaining

def getSummonerInfoByName():
	ids = []
	ids.append(getSummonerByName('dwood15')['id'])
	ids.append(getSummonerByName('imaqtpie')['id'])
	print ids
	return getSummonerLeagueEntryByIDs(ids)

print('\n')
print getSummonerInfoByName()
#get_csv_data_from_user_info()


# takes list of summoner ids as argument, supports up to 40 at a time
# (limit enforced on riot's side, no warning from code)

# returns a dictionary, mapping from summoner_id to mastery pages
# unfortunately, this dictionary can only have strings as keys,
# so must convert id from a long to a string

#print(my_mastery_pages)

#my_ranked_stats = w.get_ranked_stats(me['id'])
#print(my_ranked_stats)
#my_ranked_stats_last_season = w.get_ranked_stats(me['id'], season=2016)
#print(my_ranked_stats_last_season)

