import pymongo
from pymongo import MongoClient
import bottle
import sys
from random import randint
from bottle import route, run, template, request, response
from bson.objectid import ObjectId
from screen_info import *

RED = {"X": 1, "Y": 1}
BLUE = {"X":3, "Y":1}
def respawn(user):
    screen = get_screen(user)
    if user['team'] == 'red':
        color = RED
    else:
        color = BLUE
    user = {'_id': user["_id"], 'X': color['X'], 'Y': color['Y'], 'team':user['team'], 'x': randint(1,20), 'y': randint(1,20)}
    while not tile_is_empty(user):
        user = {'_id': user["_id"], 'X': color['X'], 'Y': color['Y'], 'team':user['team'], 'x': randint(1,20), 'y': randint(1,20)}
    
    user["health"]=100
    user["score"]=0
    user['carrying'] = 0
    user["tools"] = [1,2,3]
    user["current_tool"] = 1
    user["arrows"] = 5
    user["shield"] = False
    user["mines"] = 5
    #blowup animation
    users.update({"_id":user['_id']},{"$set": user})
    world.update({"_id":screen['_id']},{"$pull":{"users":{"_id": user["_id"]}}})
    world.update({"X":RED["X"],"Y":RED["Y"]},{"$push":{"users":user}})
