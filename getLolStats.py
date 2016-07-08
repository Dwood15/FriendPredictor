import tools
from riotwatcher import LoLException
import datetime
import MySQLdb

def insert_match(match_id, champion, season, queue, role, timestamp, lol_entity_id, cursor, db):
    # Form the SQL statement
    sql = "INSERT INTO ranked_match (match_id, champion, season, queue, role, timestamp, lol_entity_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"

    # Execute the sql statement
    try:
        cursor.execute(sql, (match_id, champion, season, queue, role, timestamp, lol_entity_id))
        db.commit()
    except MySQLdb.Error, e:
        print e.args[0], e.args[1]
        db.rollback()
    return cursor.lastrowid

def get_lol_entities(db, cursor):
    sql = "SELECT entity_id, user_id FROM lol_entity"
    try:
        cursor.execute(sql)
        db.commit()
    except MySQLdb.Error, e:
        print e.args[0], e.args[1]
        db.rollback()
    return cursor.fetchall()


def get_matches(lol_entity_id, s_id,  db, cursor):
    rw = tools.lol_connect()

    try:
        stats = rw.get_match_list(s_id)
        if 'matches' not in stats:
            return
        stats = tools.unicode_to_utf8(stats)
        for match in stats['matches']:
            match_id = match['matchId']
            champion = match['champion']
            season = match['season']
            queue = match['queue']
            role = match['role']
            timestamp = match['timestamp']
            #print match_id, champion, season, queue, role, timestamp, lol_entity_id
            insert_match(match_id, champion, season, queue, role, timestamp, lol_entity_id, cursor, db)
        print "inserted for: ", lol_entity_id
    except LoLException as e:
        return -1

    return stats


db = tools.db_connect()
cursor = db.cursor()
entity_and_user_ids = get_lol_entities(db, cursor)

for id in entity_and_user_ids:
    # print "inserting: ", id[0], id[1]
    get_matches(id[0], id[1], db, cursor)