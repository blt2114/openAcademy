import pymongo
from pymongo import MongoClient
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template, request, response
from bson.objectid import ObjectId
from screen_info import *
from spawn import *

def can_move(user,move):
    new_pos = new_coord(user,move)
    return tile_is_free(new_pos)

@route("/move", method="POST")
def move():
    user,user_id, screen = get_user_info()
    user["shield"] = False
    dir = bottle.request.json["action"]
    #if move in AXES:
    if can_move(user,dir):
        update_position(user,dir)
    else:
        users.update({"_id":user_id},{"$inc":{'health':-1}})
        users.update({"_id":user_id},{"$set":{'sound':"damage"}})
        print "invalid move"

# updates the users position as well as score and sound if as necessary
def update_position(user,move):
    screen= get_screen(user)
    new_pos= new_coord(user,move)
    user['y']=new_pos['y']
    user['x']=new_pos['x']
    #if playermove does not result in changing screens
    if ((new_pos['X']==user['X'] ) and (new_pos['Y']==user['Y'])):
        for u in screen['users']:
            if u["_id"]==user["_id"]:
                u['x']=new_pos['x']
                u['y']=new_pos['y']
                break
        world.update({"_id":screen["_id"]},{"$set":{"users":screen["users"]}})
    #else if playermove causes player to move between screens
    else:
        user['Y']=new_pos['Y']
        user['X']=new_pos['X']
        for u in screen['users']:
            if u["_id"]==user["_id"]:
                screen['users'].remove(u) 
                world.update({"_id":screen['_id']},{"$set":screen})
                break
        new_screen = get_screen(new_pos)
        new_screen['users'].append(user)
        world.update({"_id":new_screen['_id']},{"$set":new_screen})
    users.update({"_id": user["_id"]}, {"$set" : user})
    if potion_at(new_pos):
        if user['health'] < 100:
            users.update({"_id":user['_id']},{"$inc":{'health':+1}})
        users.update({"_id":user['_id']},{"$set":{'sound':"potion"}})
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'potion',"x":new_pos['x'],"y":new_pos['y']}}})
    if mine_at(new_pos):
        users.update({"_id": user['_id']},{"$inc":{'health':-50}})    
        #add sound effect here
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'mine',"x":new_pos['x'],"y":new_pos['y']}}})
    user, user_id, screen = get_user_info()
    if user["health"] <= 0:
        respawn(user)

    else:
        users.update({"_id":user['_id']},{"$inc":{'score':+1}})
        users.update({"_id":user['_id']},{"$set":{'sound':"score"}})
    #world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.'+AXES[move]:DIRECTIONS[move]}})


