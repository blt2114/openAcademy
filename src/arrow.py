import pymongo
from pymongo import MongoClient
import bottle
import sys
from bson.objectid import ObjectId
from carry import *
from spawn import *


def has_arrows(user):
    return user["arrows"] != 0 

def can_shoot(user, dir):
    if dir == "special":
        return not (carrying_tile(user))
    else:
        return has_arrows(user)

# shots an arrow from player in given direction until it hits terrain (no affect) or player (decrements health)
# fired arrows stop at edge of current screen
def shoot(user, user_id, screen, dir):
    if dir == "special":
        users.update({"_id": user_id}, {"$set":{"shield": True}})
        return
    path = []
    users.update({"_id": user_id}, {"$set":{"sound" : "laser"}})
    users.update({"_id": user_id}, {"$inc" : {"arrows":-1}})
    for magnitude in range(1,20):
        target = get_tile_coord(user,dir,magnitude)
        if (target["X"] != screen["X"]) or (target["Y"] != screen["Y"]):
            if magnitude == 1:
                return
            target = get_tile_coord(user,dir, magnitude-1)
            path.pop()
            #users.update({"_id":user_id},{"$set":{'target': {'x' : target['x'], 'y':target['y']}}})
            users.update({"X":user["X"],"Y":user["Y"]},{"$set":{'target': {'x' : target['x'], 'y':target['y']}}},multi=True)
            users.update({"X":user["X"],"Y":user["Y"]},{"$set":{'path':path}},multi=True)
            return
        # if user has just dropped a tile they will not be hit by shot
        if terrain_at(target):
            #users.update({"_id":user_id},{"$set":{'target': {'x' : target['x'], 'y':target['y']}}})
            users.update({"X":user["X"],"Y":user["Y"]},{"$set":{'target': {'x' : target['x'], 'y':target['y']}}},multi=True)
            users.update({"X":user["X"],"Y":user["Y"]},{"$set":{'path':path}},multi=True)
            return
        if user_at(target):
            is_enemy, enemy = user_at(target)
            if enemy["shield"]:
                users.update({"_id":user['_id']},{"$inc": {'health': -10}})
                user = users.find_one({"_id":user['_id']})
                if (user['health'] <= 0):
                    respawn(user)

            else:
                #users.update({"_id":user_id},{"$set":{'target': {'x' : target['x'], 'y':target['y']}}})
                users.update({"X":user["X"],"Y":user["Y"]},{"$set":{'target': {'x' : target['x'], 'y':target['y']}}},multi=True)
                users.update({"_id":enemy['_id']},{"$inc": {'health': -30}})
                enemy = users.find_one({"_id":enemy['_id']})
                if enemy["health"] <= 0:
                    respawn(enemy)
            users.update({"X":user["X"],"Y":user["Y"]},{"$set":{'path':path}},multi=True)
            return
        path.append({'x': target['x'], 'y': target['y']}) 
