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

    user_new=user.copy()
    user_new['X']=new_pos['X']
    user_new['Y']=new_pos['Y']
    user_new['x']=new_pos['x']
    user_new['y']=new_pos['y']
    write_result=world.update(
        {
            "X":user_new["X"],
            "Y":user_new["Y"],
            "tiles":{
                "$not":{
                    "$elemMatch":{
                        "x":user_new['x'],
                        "y":user_new['y'],
                        "type":"rock"
                    }
                }
            },
            "users":{
                "$not":{
                    "$elemMatch":{
                        "x":user_new['x'],
                        "y":user_new['y'],
                    }
                }
            }
        },{
            "$push":{
                "users":user_new
            }
        },
        False # no upserting
    )
    if not write_result["updatedExisting"]:
        sys.stderr.write("update of user postion failed because tile"+
        "not open\n")
        return()
    world.update(
        {
            "X":user['X'],
            "Y":user["Y"]
        },{
             "$pull":{
                "users":{
                    'x':user['x'],
                    'y':user['y']
                }
            }
        }
    )
    user=user_new
    #else if playermove causes player to move between screens
    users.update({"_id": user["_id"]}, {"$set" : user})
    users.update({"_id":user['_id']},{"$set":{'sound':"score"}})
    if potion_at(new_pos):
        if user['health'] < 100:
            users.update({"_id":user['_id']},{"$inc":{'health':+1}})
        users.update({"_id":user['_id']},{"$set":{'sound':"potion"}})
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'potion',"x":new_pos['x'],"y":new_pos['y']}}})
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
