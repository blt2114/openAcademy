import pymongo
from pymongo import MongoClient 
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template, request, response
from bson.objectid import ObjectId

SCREEN_LEN = 25 #number of spaces per row and column
WORLD_LEN = 10 #number of screens per row and column of the world


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

#this takes a user document and returns the curren screen document they are in
def get_screen(user):
    X=user['X']
    Y=user['Y']
    cur = world.find({"X":X,"Y":Y})
    if not cur.count():
        sys.stderr.write("No screen in found in current position")
        return None
    return cur[0]

#this is the route that is repeatedly called to refresh the screen
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

BUILD = {"place_tile":0, "pickup_left":1, "pickup_down": 2, "pickup_right": 3, "pickup_up": 4}#here to maintain similar structure to AXES
AXES = {"up":'y',"down":'y',"left":'x',"right":'x'}
DIRECTIONS = {"up":-1,"down":1,"left":-1,"right":1}
MOVE_DIR = {"up":(0,-1),"down":(0,1),"left":(-1,0),"right":(1,0)}
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
        users.update({"_id":user['_id']},{"$inc":{'health':+10}})
        users.update({"_id":user['_id']},{"$set":{'sound':"potion"}})
        world.update({"_id":screen['_id']},{"$pull":{"tiles":{"type":'potion',"x":new_pos['x'],"y":new_pos['y']}}})
    else:
        users.update({"_id":user['_id']},{"$inc":{'score':+1}})
        users.update({"_id":user['_id']},{"$set":{'sound':"score"}})
    #world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.'+AXES[move]:DIRECTIONS[move]}})

def update_after_pickup(user, move):
    screen = get_screen(user)
    new_pos = new_coord(user,move)
    world.update({"X":new_pos['X'],"Y":new_pos['Y']},{"$pull":{"tiles":{'x':new_pos['x'],'y':new_pos['y'],'type': 'rock'}}})

#calculates the a new desired position of a user based on direction.
# this includes both local and relative coordinates
def new_coord(user,move): 
    return get_tile_coord(user,move, 1)
    

# checks the if the position provided has a potion on it.
def potion_at(pos):
    screen = get_screen(pos)
    screen = world.find({"X":pos["X"],"Y":pos["Y"]})
    if not screen.count():
        return True
    tile = world.find({"X":pos["X"],"Y":pos["Y"],"tiles":{"type":"potion","x":pos['x'],"y":pos['y']}})
    if tile.count():
        return True
    return False

# checks the if the position provided has a rock on it.
def terrain_at(pos):
    screen = get_screen(pos)
    screen = world.find({"X":pos["X"],"Y":pos["Y"]})
    if not screen.count():
        return True
    tile = world.find({"X":pos["X"],"Y":pos["Y"],"tiles":{"type":"rock","x":pos['x'],"y":pos['y']}})
    if tile.count():
        return True
    return False

# checks if the position has a user on it.
#TODO fix so that actually checks if a user is there
def user_at(pos):
    screen = get_screen(pos)
    screen = world.find({"X":pos["X"],"Y":pos["Y"]})
    if not screen.count():
        return True
    #this currently fails because users contain other additional fields
    user = world.find({"X":pos["X"],"Y":pos["Y"],"users":{"$elemMatch":{"x":pos['x'],"y":pos['y']}}})
    if user.count():
        return True
    return False

#checks if the tile with given position is empty of players,terrain, and potion
def tile_is_empty(tile_pos):
    #tile_pos = get_tile_coord(user,dir,magnitude)
    if user_at(tile_pos) or terrain_at(tile_pos) or potion_at(tile_pos):
        return False
    return True

#checks if the tile with the tile with the given position is empyu of players and terrain
def tile_is_free(tile_pos):
    if user_at(tile_pos) or terrain_at(tile_pos):
        return False
    return True

#retrieves the coordinates of the tile with the given magnitude and direction from the user
def get_tile_coord(user,dir,magnitude):
    
    X = user['X']
    Y = user['Y']
    x = user['x']
    y = user['y']
    dx = 0
    dy = 0
    if dir in MOVE_DIR:
        dx = MOVE_DIR[dir][0]*magnitude
        dy = MOVE_DIR[dir][1]*magnitude
    
    if (x+dx) < 0:
        X -= 1
    elif (x+dx) >= SCREEN_LEN:
        X += 1
    x = (x+dx) % SCREEN_LEN
    if (y+dy) < 0:
        Y -= 1
    elif (y+dy) >= SCREEN_LEN:
        Y += 1
    y = (y+dy)%SCREEN_LEN
    return {"X":X,"Y":Y,"x":x,"y":y}

#TODO: potentially add functionality allow different users to move on
#different terrain types '''
def can_move(user,move):
    new_pos = new_coord(user,move)
    return tile_is_free(new_pos)

#return whether or not a tile can be placed at location of user
def can_place_tile(user):
    user_pos = get_tile_coord(user,"nowhere", 0)
    if carrying_tile(user):
        return not (terrain_at(user_pos))
    return False

def can_pickup_tile(user,dir):
    print dir
    pickup_pos = get_tile_coord(user,dir,1)
    if terrain_at(pickup_pos) and not(carrying_tile(user)):
        return True
    return False

def carrying_tile(user):
    return user["carrying"] != 0

# finds specific user by its _id field
def find_user(user_id):
    user =users.find_one({"_id":user_id})
    return user
def get_user_info():
    user_id = None
    if request.get_cookie("user_id"):
        user_id_str=request.get_cookie("user_id")
        user_id = ObjectId(user_id_str)
    user = users.find_one({"_id": user_id})
    if (not user):
        sys.stderr.write("User not Found!")
        return
    
    screen = get_screen(user)
    return user, user_id, screen

@route("/move", method="POST")
def move():
    user,user_id, screen = get_user_info()
    move = bottle.request.json["action"]
    if move in AXES:
        if can_move(user,move):
            update_position(user,move)
        else:
            users.update({"_id":user_id},{"$inc":{'health':-1}})
            users.update({"_id":user_id},{"$set":{'sound':"damage"}})
            print "invalid move"
    else:
        return

@route("/act", method = "POST")
def act():
    user, user_id, screen = get_user_info()
    act = bottle.request.json["action"]
    if act in BUILD:
        if act == 'place_tile': 
            if can_place_tile(user):
                output = world.update({"X":user["X"],"Y":user["Y"]},{"$push":{"tiles":{'x':user['x'],'y':user['y'],'type':'rock'}}})
                users.update({"_id": user_id}, {'$set': {'carrying': 0}})
        elif 'pickup' in act :
            #move is picking up a tile
            dir = act.split('_')[1]
            if can_pickup_tile(user,dir):
                update_after_pickup(user,dir)
                users.update({"_id": user_id}, {'$set': {'carrying':1}})
    else:
        return

@bottle.get('/<filename>')
def serve_index(filename):
    return bottle.static_file(filename, root='/home/riaz/openAcademy/')

bottle.debug(True)
bottle.run(host='localhost', port=8080)

