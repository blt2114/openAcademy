import pymongo
from pymongo import MongoClient
import bottle
import sys
from bottle import route, run, template, request, response
from bson.objectid import ObjectId
from screen_info import *

#return whether or not a tile can be placed at the location of a user
def can_place_tile(user):
    user_pos = get_tile_coord(user,"nowhere", 0)
    if carrying_tile(user):
        return not (terrain_at(user_pos))
    return False

def can_pickup(user,dir):
    if dir == "special":
        return can_place_tile(user)
    pickup_pos = get_tile_coord(user,dir,1)
    if terrain_at(pickup_pos) and not(carrying_tile(user)):
        return True
    return False

def carrying_tile(user):
    return user.has_key("carrying") and user["carrying"] != 0

def pickup(user,user_id,dir):
    if dir == "special":
        world.update({"X":user["X"],"Y":user["Y"]},{"$push":{"tiles":{'x':user['x'],'y':user['y'],'type':'rock'}}})
        users.update({"_id": user_id}, {'$set': {'carrying': 0}})
    else:
        update_after_pickup(user,dir)
        users.update({"_id": user_id}, {'$set': {'carrying':1}})

def update_after_pickup(user, move):
    screen = get_screen(user)
    new_pos = new_user_coord(user,move)
    world.update({"X":new_pos['X'],"Y":new_pos['Y']},{"$pull":{"tiles":{'x':new_pos['x'],'y':new_pos['y'],'type': 'rock'}}})
