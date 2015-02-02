import pymongo
import bottle #micro-framework
import sys
from random import randint
from bottle import route, run, template
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
    user = {'x': randint(0,19), 'y':randint(0,19)}
    db.users.insert(user)
    user.pop('_id', None)
    print user
    return user

@bottle.get("/load_screen")
def load_screen():
    screen1 = {}
    if (world.count()==0):
        screen1['tiles'] = generate_tiles()
        user1 = create_user()
        if user1 in screen1['tiles']:
            screen1['tiles'].pop(user1)
        screen1['users'] = [user1]
        world.insert(screen1)
    screen = world.find_one()
    screen.pop('_id', None)
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

@bottle.get('/<filename>')
def serve_index(filename):
    return bottle.static_file(filename, root='/Users/briantrippe/Documents/Developer/OpenAcademy/MongoDB/')
bottle.debug(True)
bottle.run(host='localhost', port=8080)

