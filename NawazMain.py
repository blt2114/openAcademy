import pymongo
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template, request

SCREEN_LEN = 20 #number of spaces per row and column
WORLD_LEN = 10 #number of screens per row and column of the world


def generate_tiles():
    #generate 20 random tiles
    tiles=[]
    for x in range(20):
        for y in range(20):
            c = randint(1,6)
            if c >= 5:
                tiles.append({'x':x,'y':y})
    return tiles 

connection = pymongo.Connection("mongodb://localhost", safe = True)
db = connection.test
world = db.world
users = db.users

def create_user():
    user = {'x': randint(10,15), 'y':randint(10,15)}
    return user

@bottle.get("/load_screen")
def load_screen():
    screen1 = {}
    #print "loading screen"
    if (world.count()==0):
        screen1['tiles'] = generate_tiles()
        user1 = create_user()
        users.insert(user1)
        print "inserted user into user db"
        if user1 in screen1['tiles']:
            screen1['tiles'].pop(user1)
        screen1['users'] = [user1]
        world.insert(screen1)
        print "inserted screen into world db"
    #else:
    #    print "data base already has a user"
    screen = world.find_one()
    print screen['users']
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
    print "updating position"
    uid=user["_id"]
    users.update({"_id": uid}, {"$inc" : {AXES[move] : DIRECTIONS[move]}})
    world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.'+AXES[move]:DIRECTIONS[move]}})

'''#TODO update this to return new poosition including screen position and
relative position'''
def new_coord(pos,move):
    return (pos[0]+MOVE_DIR[move][0],pos[1]+MOVE_DIR[move][1])

#TODO: update to check in corrects screen
def terrain_at(pos):
    tile = world.find({"tiles":{"x":pos[0],"y":pos[1]}})
    if tile.count():
        return True
#    print "tile"
#    for doc in tile: 
#        print doc
    return False

'''#TODO: potentially add functionality allow different users to move on
different terrain types '''
def can_move(user,move):
    x = user["x"]
    y = user["y"]
    new_pos = new_coord((x,y),move)
    print "new position is:"
    print new_pos[0]
    print new_pos[1]
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
    x = user["x"]
    y = user["y"]

    screen = world.find_one()
    move = bottle.request.json['move']
    if not move in AXES:
        return

    if can_move(user,move):
        update_position(user,move)
    else:
        print "invalid move"
    '''
        user = users.find_one()
        uid =user["_id"]
        x = user["x"]
        y = user["y"]

        screen = world.find_one()
        direction = bottle.request.json['move']

        if direction == "up":
                users.update({"_id": uid}, {"$inc" : {"y" : -1}})
                world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.y':-1}});
        elif direction == "down":
                users.update({"_id": uid}, {"$inc" : {"y" : 1}})
                world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.y':1}});
        elif direction == "left":
                users.update({"_id": uid}, {"$inc" : {"x" : -1}})
                world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.x':-1}});
        elif direction == "right":
                users.update({"_id": uid}, {"$inc" : {"x" : 1}})
                world.update({"users":{"$elemMatch":{"_id":uid}}},{"$inc":{'users.$.x':1}});
        return
        '''


@bottle.get('/<filename>')
def serve_index(filename):
    return bottle.static_file(filename, root='/Users/briantrippe/Documents/Developer/OpenAcademy/MongoDB/')

bottle.debug(True)
bottle.run(host='localhost', port=8080)

