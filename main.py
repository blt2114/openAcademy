import pymongo
from pymongo import MongoClient
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template, request, response

SCREEN_LEN = 20 #number of spaces per row and column
WORLD_LEN = 10 #number of screens per row and column of the world


def generate_tiles():
    #generate tiles in random positions in 20X20 grid.  1/6 of positions
    tiles=[]
    for x in range(20):
        for y in range(20):
            c = randint(1,6)
            if c > 5:
                tiles.append({'x':x,'y':y})
    return tiles 


client=MongoClient()
world=client.game.world
users=client.game.users

def create_user():
    user = {'X':1,'Y':1,'x': randint(10,15), 'y':randint(10,15)}
    users.insert(user);
    user["str_id"]=str(user["_id"])
    users.update({"_id": user["_id"]}, {"$set" : user})
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

def get_screen(user):
    X=user['X']
    Y=user['Y']
    cur = world.find({"X":X,"Y":Y})
    if not cur.count():
        sys.stderr.write("No screen in found in current position")
        return None
    return cur[0]

@bottle.get("/load_screen")
def load_screen():
    global users
    screen1 = {}
    if (world.count()==0):
        create_world()
    # ''' if user1 in screen1['tiles']:
    #     screen1['tiles'].pop(user1)'''
    #in future this can find the user based on a cookie passed in
    #Experimenting with cookies
    user_id=None
    if request.get_cookie("visited"):
        user_str_id= request.get_cookie("visited")
        user = users.find_one({"str_id":user_str_id})
        user_id=user["_id"]
    else:
        user = create_user()
        bottle.response.set_cookie("visited", user["str_id"])
        screen = get_screen(user)
        users_in_screen=screen['users']
        users_in_screen.append(user)
        screen['users']=users_in_screen
        world.update({"_id":screen['_id']},{"$set":screen})
        user_id = user["_id"] 
    

    current_user=find_user(user_id)
    if current_user is None:
        print "user with id "+str(user_id)+" not found"
        return
    screen = get_screen(current_user)
    screen.pop('_id', None)
    for user in screen["users"]:
        user.pop('_id',None)
    return {'screen':screen}

AXES = {"up":'y',"down":'y',"left":'x',"right":'x'}
DIRECTIONS = {"up":-1,"down":1,"left":-1,"right":1}
MOVE_DIR = {"up":(0,-1),"down":(0,1),"left":(-1,0),"right":(1,0)}
def update_position(user,move):
    screen = get_screen(user)
    new_pos = new_coord(user,move)
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
    #world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.'+AXES[move]:DIRECTIONS[move]}})

#calculates the a new desired position of a user based on direction.
# this includes both local and relative coordinates
def new_coord(user,move):
    X=user['X']
    Y=user['Y']
    x=user['x']
    y=user['y']
    dx = MOVE_DIR[move][0]
    dy = MOVE_DIR[move][1]
    
    if (x+dx)<0:
        X = X-1
    elif  (x+dx)>=SCREEN_LEN:
        X = X+1
    x = (x+dx)%SCREEN_LEN
    if (y+dy)<0:
        Y = Y-1
    elif (y+dy)>=SCREEN_LEN:
        Y = Y+1
    y = (y+dy)%SCREEN_LEN
    return {"X":X,"Y":Y,"x":x,"y":y}

# checks the if the position provided has a tile on it.
def terrain_at(pos):
    screen = get_screen(pos)
    screen = world.find({"X":pos["X"],"Y":pos["Y"]})
    if not screen.count():
        return True
    tile = world.find({"X":pos["X"],"Y":pos["Y"],"tiles":{"x":pos['x'],"y":pos['y']}})
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

#TODO: potentially add functionality allow different users to move on
#different terrain types '''
def can_move(user,move):
    new_pos = new_coord(user,move)
    
    if user_at(new_pos):
        return False
    if terrain_at(new_pos):
        return False
    return True


# finds specific user by its _id field
def find_user(user_id):
    user =users.find_one({"_id":user_id})
    return user

@route("/move", method="POST")
def postResource():
    user_id=None
    if request.get_cookie("visited"):
        user_id= request.get_cookie("visited")
    user = users.find_one({"str_id":user_id})
    if (not user):
        sys.stderr.write("User Not Found!")
        return
    uid =user["_id"]
    X = user["X"]
    Y = user["Y"]
    x = user["x"]
    y = user["y"]

    screen = get_screen(user)
    move = bottle.request.json['move']
    if not move in AXES:
        return

    if can_move(user,move):
        update_position(user,move)
    else:
        print "invalid move"

@bottle.get('/<filename>')
def serve_index(filename):
    return bottle.static_file(filename, root='/Users/briantrippe/Documents/Developer/OpenAcademy/MongoDB/')

bottle.debug(True)
bottle.run(host='localhost', port=8080)

