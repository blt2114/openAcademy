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
    new_pos = new_user_coord(user,move)
    return tile_is_walkable(new_pos)

# updates the users position as well as score and sound if as necessary
def update_position(user,move):
    screen= get_screen(user)
    new_pos= new_user_coord(user,move)
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
        screen = new_screen
    users.update({"_id": user["_id"]}, {"$set" : user})
    users.update({"_id":user['_id']},{"$set":{'sound':"score"}})
    if potion_at(new_pos):
        if user['health'] < 100:
            users.update({"_id":user['_id']},{"$inc":{'health':+1}})
        users.update({"_id":user['_id']},{"$set":{'sound':"potion"}})
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'potion',"x":new_pos['x'],"y":new_pos['y']}}})
    if mine_at(new_pos):
        users.update({"_id": user['_id']},{"$inc":{'health':-50}})    
        #add sound effect here
        users.update({"_id":user['_id']},{"$set":{'sound':"mine"}})
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'mine',"x":new_pos['x'],"y":new_pos['y']}}})
    if lava_at(new_pos, user['team']):
        users.update({"_id": user['_id']},{"$inc":{'health':-50}})     
    if user["health"] <= 0:
        respawn(user)
    else:
        users.update({"_id":user['_id']},{"$inc":{'score':+1}})
    #world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.'+AXES[move]:DIRECTIONS[move]}})


