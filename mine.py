import pymongo
from pymongo import MongoClient
import bottle
import sys
from bson.objectid import ObjectId
from carry import *


def has_mines(user):
    if "mines" in user:
        return user["mines"] > 0
    return False

def can_lay_mine(user, dir):
    user_pos = get_tile_coord(user,"nowhere", 0)
    if dir == "special":
        return has_mines(user) and not(terrain_at(user_pos)) and not (carrying_tile(user))
    return False

#shots an arrow from player in given direction until it hits terrain (no affect) or player (decrements health)
#fored arrpws stp[ at edge of current screen
def lay_mine(user):
    world.update({"X":user["X"], "Y":user["Y"]}, {"$push": {"tiles":{'x':user['x'],'y':user['y'],'type':'mine'}}})
    users.update({"_id": user['_id']}, {"$inc" : {"mines":-1}})
