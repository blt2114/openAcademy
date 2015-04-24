import pymongo
from pymongo import MongoClient
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template, request, response
from bson.objectid import ObjectId
from screen_info import *
from spawn import *
from mine import *

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
    if p_arrow_at(new_pos):
        if user['arrows'] < 10:
            users.update({"_id":user['_id']},{"$inc":{'arrows':+1}})
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'p_arrow',"x":new_pos['x'],"y":new_pos['y']}}})
    if p_mine_at(new_pos):
        if user['mines'] < 10:
            users.update({"_id":user['_id']},{"$inc":{'mines':+1}})
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'p_mine',"x":new_pos['x'],"y":new_pos['y']}}})
    if mine_at(new_pos):
        users.update({"_id": user['_id']},{"$inc":{'health':-100}})    
        #add sound effect here
        #blocks = world.find_one({'X':new_pos['X'],'Y':new_pos['Y']}, {'tiles': 1})
        person = users.find_one({"current_mine":{'X':new_pos['X'],'Y':new_pos['Y'],'x':new_pos['x'],'y':new_pos['y']}})
        det_mine(person)
        #users.update({"_id":user['_id']},{"$set":{'sound':"mine"}})
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'mine',"x":new_pos['x'],"y":new_pos['y']}}})
    if lava_at(new_pos, user['team']):
        users.update({"_id": user['_id']},{"$inc":{'health':-50}})     
    user = users.find_one({'_id':user['_id']})
    if user["health"] <= 0:
        respawn(user)
    else:
        users.update({"_id":user['_id']},{"$inc":{'score':+1}})
    #world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.'+AXES[move]:DIRECTIONS[move]}})


