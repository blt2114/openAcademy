import pymongo
from pymongo import MongoClient 
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template, request, response
from bson.objectid import ObjectId
from arrow import *
from carry import *
from move import *
from screen_info import *


if len(sys.argv) is not 2:
    print "please provide webroot as argument: python main.py <web_root>"
    sys.exit(2)
web_root=sys.argv[1]
SCREEN_LEN = 25 #number of spaces per row and column
WORLD_LEN = 10 #number of screens per row and column of the world
TOOLS = {1: "pickup", 2: "bow"}

def generate_tiles():
    #generate tiles in random positions in SCREEN_LENXSCREEN_LEN  grid.  1/6 of positions
    tiles=[]
    for x in range(SCREEN_LEN):
        for y in range(SCREEN_LEN):
            c = randint(1,6)
            if c > 5:
                tiles.append({'type':"rock",'x':x,'y':y})
            elif c>4:
                tiles.append({'type':"potion",'x':x,'y':y})
    return tiles 

# establish connection with game db
client=MongoClient()
world=client.game.world
users=client.game.users

def create_user():
    print "creating user"
    user = {'X':1,'Y':1,'x': randint(10,15), 'y':randint(10,15)}
    user["health"]=100
    user["score"]=0
    user['carrying'] = 0
    user["tools"] = [1,2]
    user["current_tool"] = 1
    user["arrows"] = 5
    user["shield"] = False
    users.insert(user)
    return user

def create_world():
    for X in range(WORLD_LEN):
        for Y in range(WORLD_LEN):
            screen = {}
            screen['tiles'] = generate_tiles()
            screen['X']=X
            screen['Y']=Y
            screen['users']=[]
            if world.find({'X':X,'Y':Y}).count():
                sys.stderr.write("screen in this position already exists.")
                continue
            world.insert(screen)

@bottle.get("/load_screen")
def load_screen():
    screen1 = {}
    if (world.count()==0):
        create_world()
    user_id=None
    current_user=None
    user_id_str= request.get_cookie("user_id")
    if user_id_str:
        user_id = ObjectId(user_id_str)
        current_user=find_user(user_id)
        if current_user is None:
            print "user with id "+str(user_id)+" not found, creating new"
            "user"
    #if either the cookie does not exist or the user is not found
    if current_user is None:
        current_user = create_user()
        user_id=current_user["_id"]
        bottle.response.set_cookie("user_id", str(user_id))
        screen = get_screen(current_user)
        screen['users'].append(current_user)
        world.update({"_id":screen['_id']},{"$set":screen})

    screen = get_screen(current_user)
    
    sound = None
    if "sound" in current_user:
        sound=current_user["sound"]
        current_user.pop("sound")
    screen.pop('_id', None)
    for user in screen["users"]:
        user.pop('_id')
        user.pop('Y')
        user.pop('X')
    screen.pop('X')
    screen.pop('Y')
    current_user['_id']=str(current_user['_id'])
    users.update({"_id":user_id},{"$unset":{'sound':""}})
    return {'screen':screen,'player':current_user,"sound":sound}

#BUILD = {"place_tile":0, "pickup_left":1, "pickup_down": 2, "pickup_right": 3, "pickup_up": 4}#here to maintain similar structure to AXES
#AXES = {"up":'y',"down":'y',"left":'x',"right":'x'}
PICKUP = ["pickup_left","pickup_right","pickup_up","pickup_down", "pickup_special"]
#AXES = ["up", "down", "left", "right"]
DIRECTIONS = {"up":-1,"down":1,"left":-1,"right":1}
@route("/act", method = "POST")
def act():
    user, user_id, screen = get_user_info()
    users.update({"_id": user_id}, {"$set": {"shield" : False}})
    dir = bottle.request.json["action"]
    tool = TOOLS[user["current_tool"]]
    print tool
    if tool== "pickup":
        if can_pickup(user, dir):
            pickup(user,user_id, dir)
        else:
            print "invalid_pickup"
    elif tool == "bow":
        if can_shoot(user, dir):
            shoot(user, user_id,screen, dir)
        else:
            print "invalid_shoot"
    else:
        return
@route("/switch", method = "POST")
def switch():
    user, user_id, screen = get_user_info()
    tool = int(bottle.request.json["action"])
    users.update({"_id": user_id}, {'$set': {"current_tool": tool}})

@bottle.get('/<filename>')
def serve_index(filename):
    return bottle.static_file(filename, root=web_root)

bottle.debug(True)
bottle.run(host='localhost', port=8080)

