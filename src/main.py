import pymongo
from pymongo import MongoClient 
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template, request, response
from bson.objectid import ObjectId
from arrow import *
from mine import *
from carry import *
from move import *
from build import *
from screen_info import *

SCREEN_LEN = 25 #number of spaces per row and column
#WORLD_LEN = 10 #number of screens per row and column of the world
WORLD_LEN = 3
TOOLS = {1: "pickup", 2: "bow", 3: "mine", 4: "build"}
INITIAL_HEALTH = 100
INITIAL_SCORE = 0
INITIAL_MINES = 5
INITIAL_ARROWS = 5
TEAM_1_COLOR="red"
TEAM_2_COLOR="blue"

rock_freq=0.13
potion_freq=0.05
mine_freq=0.02
arrow_freq=0.05

if len(sys.argv) is not 3:
    print "invalid use: python main.py <web_root> <port>"
    sys.exit(2)
web_root=sys.argv[1]
port=int(sys.argv[2])

# generates a tiles array, for an arbitrary screen or for a base if
# base_color is given. If the postion given is on the end of the world, then
# set the walls on that edge to rocks
def generate_tiles(base_color,X,Y):
    #generate tiles in random positions in SCREEN_LENXSCREEN_LEN  grid.  1/6 of positions
    tiles=[]
    is_base = False
    if base_color != '':
        is_base = True
    for x in range(SCREEN_LEN):
        if X==0 and x == 0:
            for y in range(SCREEN_LEN):
                tiles.append({'type':"rock",'x':x,'y':y})
            continue
        if X==WORLD_LEN-1 and x == SCREEN_LEN-1:
            for y in range(SCREEN_LEN):
                tiles.append({'type':"rock",'x':x,'y':y})
            continue
        for y in range(SCREEN_LEN):
            if Y==WORLD_LEN-1 and y==SCREEN_LEN-1:
                tiles.append({'type':"rock",'x':x,'y':y})
                continue
            if Y==0 and y==0:
                tiles.append({'type':"rock",'x':x,'y':y})
                continue
            if is_base and x in range(SCREEN_LEN/2-1,SCREEN_LEN/2+2) and y in range(SCREEN_LEN/2-1,SCREEN_LEN/2+2):
                tiles.append({'type': base_color + '_base','x': x, 'y': y, 'health': 200})
                #tiles.append({'type': base_color + '_base','x': x, 'y': y})
            #randomly place rocks, potions, and arrows/mines for pickup around the screen
            else:
                c = randint(1,100)
                if c < 100*rock_freq:
                    tiles.append({'type':"rock",'x':x,'y':y})
                    continue
                c = randint(1,100)
                if c < 100*potion_freq:
                    tiles.append({'type':"potion",'x':x,'y':y})
                    continue
                c = randint(1,100)
                if c < 100*arrow_freq:
                    tiles.append({'type':"p_arrow",'x':x,'y':y})
                    continue
                c = randint(1,100)
                if c < 100*mine_freq:
                    tiles.append({'type':"p_mine",'x':x,'y':y})
    return tiles 

# establish connection with game db
client=MongoClient()
world=client.game.world
users=client.game.users
RED = {'X': 0, 'Y': 1}
BLUE = {'X':2, 'Y': 1}
def create_user():
    print "creating user"
    red_users = users.find({"team":TEAM_1_COLOR}).count()
    blue_users = users.find({"team":TEAM_2_COLOR}).count()
    color = RED
    if red_users > blue_users:
        color = BLUE
    user = {'X':color['X'],'Y':color['Y'],'x': randint(1,20), 'y':randint(1,20)}
    while not tile_is_empty(user):
        user = {'X':color['X'],'Y':color['Y'],'x': randint(1,20), 'y':randint(1,20)}
    if color == RED:
        user['team'] = TEAM_1_COLOR
    else:
        user['team'] = TEAM_2_COLOR
    user["health"]= INITIAL_HEALTH
    user["score"]= INITIAL_SCORE
    user['carrying'] = 0
    user["tools"] = [1,2,3,4] #Tools that the user can initially use
    user["current_tool"] = 1
    user["arrows"] = INITIAL_ARROWS
    user["shield"] = False
    user["mines"] = INITIAL_MINES
    #primed indicates whether the user has a mine deployed awaiting detonation
    user['primed'] = False
    users.insert(user)
    return user

def create_world():
    print "creating world"
    for X in range(WORLD_LEN):
        for Y in range(WORLD_LEN):
            screen = {}
            if (X == RED['X']) and (Y == RED['Y']):
                screen['tiles'] = generate_tiles(TEAM_1_COLOR,X,Y)
            elif (X == BLUE['X']) and (Y == BLUE['Y']):
                screen['tiles'] = generate_tiles(TEAM_2_COLOR,X,Y)
            else:
                screen['tiles'] = generate_tiles('',X,Y)
            
            screen['X']=X
            screen['Y']=Y
            screen['users']=[]
            screen['structures'] = []
            if world.find({'X':X,'Y':Y}).count():
                sys.stderr.write("screen in this position already exists.")
                continue
            world.insert(screen)

    

@route("/move", method="POST")
def move():
    user,user_id, screen = get_user_info(request)
    user["shield"] = False
    dir = bottle.request.json["action"]
    #if move in AXES:
    pos = new_user_coord(user, move)
    if can_move(user,dir):
        update_position(user,dir)
    else:
        users.update({"_id":user_id},{"$inc":{'health':-1}})
        users.update({"_id":user_id},{"$set":{'sound':"damage"}})
        print "invalid move"

def game_is_over():
    blueBase = False
    redBase = False
    base_screen = world.find_one({'X': BLUE['X'], 'Y':BLUE['Y']})
    for tile in base_screen['tiles']:
        if tile['type'] == 'blue_base':
            blueBase = True
            break   
    if blueBase:
        base_screen = world.find_one({'X': RED['X'], 'Y':RED['Y']})
        for tile in base_screen['tiles']:
            if tile['type'] == 'red_base':
                redBase = True
                break   
    return not (blueBase and redBase)
        
        
@bottle.get("/load_screen")
def load_screen():
    if (world.count()==0):
        create_world()

    if game_is_over():
        print "GAME OVER"
        return
    user_id=None
    current_user=None
    user_id_str= request.get_cookie("user_id")
    if user_id_str:
        user_id = ObjectId(user_id_str)
        current_user=find_user(user_id)

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
    target = None
    if "target" in current_user:
        target = current_user["target"]
        current_user.pop("target")
    path = None
    if "path" in current_user:
        path = current_user["path"]
        current_user.pop("path")
    screen.pop('_id', None)
    for user in screen["users"]:
        user.pop('_id')
        user.pop('Y')
        user.pop('X')
        user.pop('tools')
        user.pop('health')
        user.pop('carrying')
        user.pop('current_tool')
        user.pop('score')
        user.pop('mines')
        user.pop('shield')
    # go through every tile and check if it is a mine belonging to the other
    # team.  If it does, remove it and don't display it.
    num_tiles = len(screen["tiles"])
#    print "tiles before: " + str(screen["tiles"])
    for i in range(num_tiles):
        if screen["tiles"][i]["type"] == "mine" and screen["tiles"][i]["team"] != user["team"]:
            screen["tiles"]=screen["tiles"][0:i-1].extend(screen["tiles"][i:len(screen["tiles"])])
#    print "tiles after: " + str(screen["tiles"])
    screen.pop('X')
    screen.pop('Y')
    current_user['_id']=str(current_user['_id'])
    users.update({"_id":user_id},{"$unset":{'sound':""}})
    users.update({"_id":user_id},{"$unset":{'target':""}})
    users.update({"_id":user_id},{"$unset":{'path':""}})
    return {'screen':screen,'player':current_user,"sound":sound, "target":target, "path": path}

PICKUP = ["pickup_left","pickup_right","pickup_up","pickup_down", "pickup_special"]
DIRECTIONS = {"up":-1,"down":1,"left":-1,"right":1}
@route("/act", method = "POST")
def act():
    user, user_id, screen = get_user_info(request)
    users.update({"_id": user_id}, {"$set": {"shield" : False}})
    dir = bottle.request.json["action"]
    #tool = TOOLS[bottle.request.json["current_tool"]];
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
    elif tool == "mine":
        if can_lay_mine(user, dir):
            if not user['primed']:
                lay_mine(user)
            else:
                det_mine(user)
        else:
            print "invalid mine"
    elif tool == "build":
        if can_build(user,dir):
            build(user, dir)
        else:
            print "invalid build"
    else:
        return

def can_switch(user):
    return not(carrying_tile(user))

@route("/switch", method = "POST")
def switch():
    user, user_id, screen = get_user_info(request)
    if can_switch(user):    
        tool = int(bottle.request.json["action"])
        users.update({"_id": user_id}, {'$set': {"current_tool": tool}})

@bottle.get('/<filename:path>')
def serve_index(filename):
    return bottle.static_file(filename, root=web_root)

@route("/", method = "GET")
def home():
    bottle.redirect("/index.html")

bottle.debug(True)
bottle.run(host='localhost', port=port)
