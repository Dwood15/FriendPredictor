from riotwatcher import RiotWatcher

w = RiotWatcher('')

# check if we have API calls remaining
print(w.can_make_request())

me = w.get_summoner(name='imaqtpie')
print(me)
print(me['id'])
# takes list of summoner ids as argument, supports up to 40 at a time
# (limit enforced on riot's side, no warning from code)
#my_mastery_pages = w.get_mastery_pages([me['id'], ])[str(me['id'])]
# returns a dictionary, mapping from summoner_id to mastery pages
# unfortunately, this dictionary can only have strings as keys,
# so must convert id from a long to a string

#print(my_mastery_pages)

#my_ranked_stats = w.get_ranked_stats(me['id'])
#print(my_ranked_stats)

my_ranked_stats_last_season = w.get_ranked_stats(me['id'], season=2016)
print(my_ranked_stats_last_season)

