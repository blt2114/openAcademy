import pymongo
from pymongo import MongoClient
from bottle import route, run, template, request, response
import sys
from bson.objectid import ObjectId


client=MongoClient()
world=client.game.world
users=client.game.users
SCREEN_LEN = 25
WORLD_LEN = 10
MOVE_SPEED = 1 # the number of tiles user move at a time

#calculates the a new desired position of a user based on direction.
# this includes both local and relative coordinates
def new_user_coord(user,move): 
    return get_tile_coord(user,move, MOVE_SPEED)

#this takes a user document and returns the curren screen document they are in
def get_screen(user):
    X=user['X']
    Y=user['Y']
    cur = world.find({"X":X,"Y":Y})
    if not cur.count():
        sys.stderr.write("No screen in found in current position")
        return None
    return cur[0]
def potion_at(pos):
    screen = get_screen(pos)
    screen = world.find({"X":pos["X"],"Y":pos["Y"]})
    if not screen.count():
        return True
    tile = world.find({"X":pos["X"],"Y":pos["Y"],"tiles":{"type":"potion","x":pos['x'],"y":pos['y']}})
    if tile.count():
        return True
    return False

def lava_at(pos, team):
    color = 'red'
    print "team", team
    if team == 'red':
        color = 'blue' 
    screen = get_screen(pos)
    screen = world.find({"X":pos["X"],"Y":pos["Y"]})
    if not screen.count():
        return True 
    tile = world.find({"X":pos["X"],"Y":pos["Y"],"tiles":{"type":color +"_lava","x":pos['x'],"y":pos['y']}})
    if tile.count():
        return True
    return False
def mine_at(pos):
    screen = get_screen(pos)
    screen = world.find({"X":pos["X"],"Y":pos["Y"]})
    if not screen.count():
        return True 
    tile = world.find({"X":pos["X"],"Y":pos["Y"],"tiles":{"type":"mine","x":pos['x'],"y":pos['y']}})
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

def rock_at(pos):
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
        return False
        #return True
    #this currently fails because users contain other additional fields
    users = world.find_one({"X":pos["X"],"Y":pos["Y"],"users":{"$elemMatch":{"x":pos['x'],"y":pos['y']}}},{"_id": 0, "users":1})
    #print "users", users
    if users:
        for user in users["users"]:
            #print "user", user
            if user['x'] == pos['x'] and user['y'] == pos['y']:
                return True, user
    #if user.count():
        #return True, user[0]
    return False

#checks if the tile with given position is empty of players,terrain, and potion
def tile_is_empty(tile_pos):
    #tile_pos = get_tile_coord(user,dir,magnitude)
    if user_at(tile_pos) or terrain_at(tile_pos) or potion_at(tile_pos):
        return False
    return True

#checks if the tile with the tile with the given position is empyu of players and terrain
def tile_is_walkable (tile_pos):
    if user_at(tile_pos) or terrain_at(tile_pos):
        return False
    return True

#retrieves the coordinates of the tile with the given magnitude and direction from the user
MOVE_DIR = {"up":(0,-1), "down": (0,1), "left": (-1,0), "right":(1, 0)}
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


def find_user(user_id):
    user =users.find_one({"_id":user_id})
    return user

def get_user_info( request):
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
