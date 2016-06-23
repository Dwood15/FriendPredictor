import tools
import re
import MySQLdb


def get_names(data):
    print data
    for bio in data:
        keywords = [' ign: ', ' summoner name: ', ' IGN: ', ' IGN :', ' in game name: ', ' lol name: ', ' league of legends username: ', ' league of legends name: ', ' IG:', ' IG: ', 'ig:', 'ig: ']
        for keyword in keywords:
            text_before, my_keyword, text_after = bio[0].partition(keyword)
            # print bk, '-STOP-', k,'-STOP-', ak
            if my_keyword:
                text_after_split = text_after.split(' ')
                lol_name = text_after_split[0] if len(text_after_split[0]) > 1 else text_after_split[1]
                print "MATCH: ", lol_name, " keyword matched ", keyword, " on: ", my_keyword
            else:
                print "no match: ", bio[0]


def query_ign():
    db = tools.db_connect()
    cursor = db.cursor()
    try:
        sql = r"SELECT description FROM twitter_entity WHERE description LIKE '% summoner name: %' OR description LIKE '% IGN: %' OR description LIKE '% in game name: %' OR description LIKE '% lol name: %' OR description LIKE '% league of legends username: %' OR description LIKE '% league of legends name: %' OR description LIKE '% IGN : %' OR description LIKE '% IG: %'"
        # sql = r"select SUBSTRING_INDEX(description,'ign:',1) from twitter_entity"

        print sql
        cursor.execute(sql)
        data = cursor.fetchall()
        print len(data), " results"
        get_names(data)
    except MySQLdb.MySQLError as e:
        print "Error: unable to fetch data: ", e
    db.close()


# query_ign()

get_names((("They warned me about drugs, but they didn't warn me about the one with hazel eyes and black hair | IG: itselleeen | Bethany Mota",), ('Just Your Average Dank Memer \n\nLeague PH IGN : Naegi \nDiamond/Master Player',)))
