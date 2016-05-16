import csv

uInfoFile = 'userInfo.csv'
''' Ideally this info will be parsed into the following format (cutting information we may not care about)
{"19887289": [{
   "queue": "RANKED_SOLO_5x5",
   "name": "Sivir's Defiants",
   "entries": [{
      "leaguePoints": 504,
      "isFreshBlood": false,
      "isHotStreak": true,
      "division": "I",
      "isInactive": false,
      "isVeteran": false,
      "losses": 68,
      "playerOrTeamName": "Imaqtpie",
      "playerOrTeamId": "19887289",
      "wins": 110
   }],
   "tier": "CHALLENGER"
   
   Becomes:
   PlayerID, Queue, "PlayerName", "PlayerorTeamName", "Division", "Tier"
   19887289,  RANKED_SOLO_5x5,  Imaqtpie, Imaqtpie, 1, CHALLENGER
}]}
'''
#TODO: Validation?

def get_csv_data_from_user_info(userName, userInfo):
	players = []
	for uID in userInfo.keys():
		values = {}
		curr = userInfo[uID]
		values['UserId'] = uID
		values['Queue'] = curr['queue']
		values['Division'] =curr['entries']['division']
		values['PlayerName'] = userName
		players.append(values)
		
	return players
	
seasonMatchUserFile = 'matchInfos.csv'



def saveUserInfo():
	pass