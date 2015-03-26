import pymongo
from pymongo import MongoClient
import bottle
import sys
from bson.objectid import ObjectId
from carry import *


def has_arrows(user):
    return user["arrows"] != 0 

def can_shoot(user, dir):
    if dir == "special":
        return not (carrying_tile(user))
    else:
        return has_arrows(user)

#shots an arrow from player in given direction until it hits terrain (no affect) or player (decrements health)
#fored arrpws stp[ at edge of current screen
def shoot(user, user_id, screen, dir):
    if dir == "special":
        users.update({"_id": user_id}, {"$set":{"shield": True}})
        return
    users.update({"_id": user_id}, {"$inc" : {"arrows":-1}})
    for magnitude in range(1,20):
        target = get_tile_coord(user,dir,magnitude)
        if (target["X"] != screen["X"]) or (target["Y"] != screen["Y"]):
            return
        #if user has just dropped a tile they will not be hit by shot
        if terrain_at(target):
            return
        if user_at(target):
            is_enemy, enemy = user_at(target)
            if enemy["shield"]:
                user["health"] -= 1
            else:
                enemy["health"] -= 1
