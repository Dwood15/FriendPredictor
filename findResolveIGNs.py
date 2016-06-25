import string
import tools
import MySQLdb
import time
from riotwatcher import LoLException


def is_lol_player(s_name):
    rw = tools.lol_connect()
    try:
        # print "Calling API: "
        me = rw.get_summoner(name=s_name)
    except LoLException as e:
        return -1

    return me


def contains_punc(my_string):
    check_array = [j in string.punctuation for j in my_string]
    if True in check_array:
        return True
    else:
        return False


def resolve(twitter_entity):
    # print "passed in entity: ", twitter_entity
    bio = twitter_entity[3]
    print bio
    keywords = ['lol name: ', 'lol ign:', 'lol ign :', 'league ign:','league ign :', 'summoner name: ', 'summoner name : ', 'league of legends username: ',
                'league of legends name: ', 'ign:', 'ign :', 'find me ig:', 'in game name: ', 'in game name : ']
    for keyword in keywords:
        text_before, my_keyword, text_after = bio.lower().partition(keyword)

        if my_keyword:

            # Check for other possible game lables here
            word_before = text_before.split(' ')[-2]
            print "Text before -1", word_before
            if 'minecraft' in word_before or 'mc' in word_before or 'garnea' in word_before or 'xbox' in word_before or 'runescape' in word_before:
                print "minecraft ign"
                continue

            # Attempt to parse out the summoner name
            text_after_split = text_after.split(' ')
            lol_name = text_after_split[0]
            print "got this for lol name: ", lol_name
            # Summoner Names cannot be shorter than 4 chars in length
            i = 1
            while len(lol_name) < 4 and i < len(text_after_split):
                lol_name = lol_name + text_after_split[i]
                # print "less than 4! adding the rest name is now: ", lol_name
                i += 1
            # if there is still more in text_after_split, step through one char at a time to see if the next word is part of the username
            # For the most part pieces of desc are separated by punc. If assumed lol_name contains punc, we can skip this
            # Otherwise we should check to see if the next word also contains punc and add it to the name if not.
            # Also don't add the next word if it starts with a new line
            if i < len(text_after_split) and not contains_punc(lol_name):
                print i, len(text_after_split), text_after_split[i], not contains_punc(text_after_split[i])
                while i is not len(text_after_split) and not contains_punc(text_after_split[i]) and not \
                text_after_split[i].startswith('\n'):
                    lol_name = lol_name + text_after_split[i]
                    i += 1

            # Remove last character if punc
            if lol_name[-1] is '.' or lol_name[-1] is ',':
                lol_name = lol_name[:-1]
            # print "MATCH: ", lol_name, " keyword matched ", keyword, " on: ", my_keyword
            if lol_name:
                player = is_lol_player(lol_name)
                if player != -1:
                    return player
                else:
                    return -1
            else:
                continue
    print "no match in keywords: ", bio
    return -1


def insert_entity(res, cursor, db):
    res_utf8 = tools.unicode_to_utf8(res)
    summoner_name = res_utf8['name']
    level = res_utf8['summonerLevel']
    user_id = res_utf8['id']
    print summoner_name, level, user_id
    # Form the SQL statement
    sql = "INSERT INTO lol_entity (summoner_name, level, user_id) VALUES (%s, %s, %s)"

    # Execute the sql statement
    try:
        cursor.execute(sql, (summoner_name, level, user_id))
        db.commit()
    except MySQLdb.Error, e:
        print e.args[0], e.args[1]
        db.rollback()
    return cursor.lastrowid


def insert_resolution(lol_id, twitter_id, cursor, db):
    # Form the SQL statement
    sql = "INSERT INTO twitter_lol_resolution (lol_entity_id, twitter_entity_id) VALUES (%s, %s)"

    # Execute the sql statement
    try:
        cursor.execute(sql, (lol_id, twitter_id))
        db.commit()
    except MySQLdb.Error, e:
        print e.args[0], e.args[1]
        db.rollback()
    return cursor.lastrowid


def query_ign():
    db = tools.db_connect()
    cursor = db.cursor()
    check_file = open('check.txt', 'a')
    try:
        sql = r"SELECT * FROM twitter_entity WHERE description LIKE '% summoner name : %' OR description LIKE '% summoner name: %' OR description LIKE '% IGN: %' OR description LIKE '% in game name: %' OR description LIKE '% lol name: %' OR description LIKE '% league of legends username: %' OR description LIKE '% league of legends name: %' OR description LIKE '% IGN : %' OR description LIKE '% Find me IG: %'"
        print sql
        cursor.execute(sql)
        data = cursor.fetchall()
        print len(data), " results"
        counter = 0
        for twitter_entity in data:
            res = resolve(twitter_entity)
            if res is -1:
                check_file.write(str(twitter_entity))
                print "player does not exist"
            else:
                insert_id = insert_entity(res, cursor, db)
                insert_resolution(insert_id, twitter_entity[0], cursor, db)

                counter += 1

            print "\n --END--\n"
            time.sleep(2)



    except MySQLdb.MySQLError as e:
        print "Error: unable to fetch data: ", e
    print "resolved: ", counter
    db.close()


query_ign()
