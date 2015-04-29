import pymongo
from pymongo import MongoClient
import bottle
import sys
from bson.objectid import ObjectId
from carry import *
from  spawn import *


def has_mines(user):
    if "mines" in user:
        return user["mines"] > 0
    return False

def can_lay_mine(user, dir):
    user_pos = get_tile_coord(user,"nowhere", 0)
    if dir == "special" and user['primed']:
        return True
    if dir == "special":
        return has_mines(user) and not(terrain_at(user_pos)) and not (carrying_tile(user))
    return False

#shots an arrow from player in given direction until it hits terrain (no affect) or player (decrements health)
#fored arrpws stp[ at edge of current screen
def lay_mine(user):
    a = 'a' + str(user["_id"])
    #world.update({"X":user["X"], "Y":user["Y"]}, {"$push": {"tiles":{'x':user['x'],'y':user['y'],'type':'mine', 'mine_of' : a}}})
    world.update({"X":user["X"], "Y":user["Y"]}, {"$push": {"tiles":{'x':user['x'],'y':user['y'],'type':'mine'}}})
    users.update({"_id": user['_id']}, {"$inc" : {"mines":-1}})
    users.update({"_id": user['_id']}, {"$set" : {"current_mine":{'X':user['X'], 'Y': user['Y'],'x': user['x'], 'y': user['y']}}})
    users.update({'_id':user['_id']},{'$set': {'primed': True}})

    
def det_mine(user):
    mine = user['current_mine']
    adj_pos = []
    adj_pos.append(get_tile_coord(mine, 'left', 1))
    adj_pos.append(get_tile_coord(mine, 'right', 1))
    adj_pos.append(get_tile_coord(mine, 'up', 1))
    adj_pos.append(get_tile_coord(mine, 'down', 1))

    for p in adj_pos:
        if user_at(p):
            temp, enemy = user_at(p)
            users.update({'_id': enemy['_id']}, {"$inc": {'health': -50}})
            if enemy['health'] <= 50:
                respawn(enemy)
        elif terrain_at(p):

            world.update({'X':p['X'],'Y':p['Y']},{'$pull':{'tiles' : { 'x':p['x'] , 'y':p['y'], 'type': {'$exists':'true'}}}})
            #world.update({'X':p['X'],'Y':p['Y']},{'$pull':{"$and": [{'tiles' : { 'x':p['x']}},{'tiles':{'y':p['y']}}]}})
            #world.update({'X':p['X'],'Y':p['Y']},{'$pull':{'tiles.x' : p['x'], 'tiles.y':p['y']}})

    world.update({'X':mine['X'],'Y':mine['Y']},{'$pull':{'tiles':{'x':mine['x'],'y':mine['y'],'type':'mine'}}})

    users.update({"_id":user['_id']},{'$unset':{'current_mine':''}})
    #users.update({'_id':user['_id']},{'$set':{'sound':'mine'}})
    users.update({"X":user["X"],"Y":user["Y"]},{'$set':{'sound':'mine'}},multi=True)
    users.update({'_id':user['_id']},{'$set':{'primed':False}})
    a = 'a'+str(user["_id"])

