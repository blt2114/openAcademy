import pymongo
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template, request

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

connection = pymongo.Connection("mongodb://localhost", safe = True)
db = connection.test
world = db.world
users = db.users

def create_user():
    user = {'X':1,'Y':1,'x': randint(10,15), 'y':randint(10,15)}
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
    screen1 = {}
    if (world.count()==0):
        create_world()
        user1 = create_user()
        print "about to insert user"+str(user1)
        users.insert(user1)
        print "just inserted user:"+str(user1)
        screen = get_screen(user1)
        users=screen['users']
        users.append(user)
        screen['users']=users
        world.update({"_id":screen['_id']},{"$set":screen})
      # ''' if user1 in screen1['tiles']:
       #     screen1['tiles'].pop(user1)'''
    #in future this can find the user based on a cookie passed in
    current_user=find_user()
    screen = get_screen(current_user)
    screen.pop('_id', None)
    for user in screen["users"]:
        user.pop('_id',None)
    return {'screen':screen}

# not used
@bottle.get("/generate_screen")
def build_screen():
    screen1 = {}
    screen1['tiles'] = generate_tiles()
    screen1['users'] = [{'x': 0, 'y':0}]
    db.world.insert(screen1)
    screen1.pop('_id', None)
    return {'screen':screen1}

AXES = {"up":'y',"down":'y',"left":'x',"right":'x'}
DIRECTIONS = {"up":-1,"down":1,"left":-1,"right":1}
MOVE_DIR = {"up":(0,-1),"down":(0,1),"left":(-1,0),"right":(1,0)}
def update_position(user,move):
    screen = get_screen(user)
    new_pos = new_coord(user,move)
    user['Y']=new_pos['Y']
    user['y']=new_pos['y']
    user['X']=new_pos['X']
    user['x']=new_pos['x']
    if ((new_pos['X']==user['X'] )& (new_pos['Y']==user['Y'])):
        for u in screen['users']:
            if u["_id"]==user["_id"]:
                u['x']=new_pos['x']
                u['y']=new_pos['y']
                break
        world.update({"_id":screen["_id"]},{"$set":{"users":screen["users"]}})
    else:
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

'''#TODO update this to return new poosition including screen position and
relative position'''
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

#TODO: update to check in corrects screen
def terrain_at(pos):
    screen = get_screen(pos)
    screen = world.find({"X":pos["X"],"Y":pos["Y"]})
    if not screen.count():
        return True
    tile = world.find({"X":pos["X"],"Y":pos["Y"],"tiles":{"x":pos['x'],"y":pos['y']}})
    if tile.count():
        return True
    return False

'''#TODO: potentially add functionality allow different users to move on
different terrain types '''
def can_move(user,move):
    new_pos = new_coord(user,move)
    print "new position is:"+str(new_pos)
    return not terrain_at(new_pos)


#TODO: add functionality to look up specific user based on browser cookie .
def find_user():
    user =users.find_one()
    return user

@route("/move", method="POST")
def postResource():
    user = find_user()
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

